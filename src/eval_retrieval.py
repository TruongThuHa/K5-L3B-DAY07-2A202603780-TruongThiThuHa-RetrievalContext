"""Bước C · Đánh giá retrieval + context trên cùng corpus, cùng câu hỏi, cùng định nghĩa hit.

    python -m src.eval_retrieval --split dev
    python -m src.eval_retrieval --split test --locked     # CHỈ chạy sau khi đã commit chốt cấu hình

Chỉ số (mẫu số = số câu CÓ đáp án; câu thiếu bằng chứng không tính vào đây):
    Hit@1           : chunk hạng 1 chứa evidence đúng nguồn + trang
    Evidence Hit@3  : 1 trong 3 chunk đầu chứa evidence
    Context Evidence: context cuối (sau khi cắt theo budget ký tự) còn chứa chunk có evidence
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

from .retrievers import ROOT, BM25Retriever, DenseRetriever, HybridRetriever, RerankRetriever, load_chunks

sys.path.insert(0, str(ROOT / "starter"))
from baseline import TfidfIndex, hit, pack_context  # noqa: E402  (dùng lại đúng định nghĩa hit/context của đề)

QUESTIONS = ROOT / "data" / "he2020" / "questions.json"
RESULTS = ROOT / "results" / "retrieval"

# Tên cấu hình -> (retriever, top_k, context budget ký tự, giả thuyết)
def build_configs(names: list[str]) -> dict:
    chunks = load_chunks()
    dense, bm25 = DenseRetriever(), BM25Retriever(chunks)
    hybrid = HybridRetriever(dense, bm25)
    lazy = {}

    class Tfidf:  # bọc TF-IDF của starter cho cùng giao diện (TF-IDF starter không hỗ trợ filter)
        method = "tfidf"
        index = TfidfIndex(chunks)

        def search(self, query, *, filters=None, top_k=3):
            return [{**c, "rank": i} for i, c in enumerate(self.index.search(query, top_k), start=1)]

    def rerank():
        if "rerank" not in lazy:
            lazy["rerank"] = RerankRetriever(hybrid)
        return lazy["rerank"]

    table = {
        "tfidf":            (lambda: Tfidf(), 3, 800, "Baseline của đề (lexical TF-IDF), không filter"),
        "dense":            (lambda: dense, 3, 800, "BASELINE: dense Day 6 (cấu hình C: chunk B + filter section)"),
        "bm25":             (lambda: bm25, 3, 800, "PP2: BM25 bắt được số liệu, tên riêng mà dense bỏ sót"),
        "hybrid":           (lambda: hybrid, 3, 800, "PP3: RRF dense + BM25 bù lỗi cho nhau"),
        "hybrid_rerank":    (lambda: rerank(), 3, 800, "CẢI THIỆN 1: rerank 20 ứng viên hybrid bằng cross-encoder"),
        "hybrid_rerank_b2400": (lambda: rerank(), 3, 2400, "CẢI THIỆN 2: budget 800 chỉ vừa ~1 chunk -> tăng lên 2400"),
    }
    unknown = set(names) - set(table)
    if unknown:
        raise SystemExit(f"Không có cấu hình {sorted(unknown)}. Có: {sorted(table)}")
    return {n: (table[n][0](), *table[n][1:]) for n in names}


def evaluate(name, retriever, top_k, budget, questions):
    traces = []
    for q in questions:
        start = time.perf_counter()
        results = retriever.search(q["question"], filters=q.get("filter"), top_k=max(top_k, 3))
        elapsed_ms = (time.perf_counter() - start) * 1000
        context, ids = pack_context(results[:top_k], budget=budget)
        marked = [{"rank": r["rank"], "id": r["id"], "page": r["page"], "section": r["metadata"].get("section"),
                   "score": r["score"], "hit": hit(r, q["gold"])} for r in results]
        traces.append({"config": name, "query_id": q["id"], "split": q["split"], "question": q["question"],
                       "filter": q.get("filter"), "top_k": top_k, "budget_chars": budget,
                       "gold_pages": sorted({g["page"] for g in q["gold"]}), "results": marked,
                       "context_ids": ids, "context_chars": len(context), "elapsed_ms": round(elapsed_ms, 1),
                       "hit1": bool(marked and marked[0]["hit"]),
                       "hit3": any(m["hit"] for m in marked[:3]),
                       "context_hit": any(m["hit"] and m["id"] in ids for m in marked)})
    n = len(traces)
    pct = lambda k: f"{sum(t[k] for t in traces)}/{n} ({100 * sum(t[k] for t in traces) / n:.0f}%)"
    summary = {"config": name, "method": retriever.method, "top_k": top_k, "budget_chars": budget, "n": n,
               "hit1": pct("hit1"), "evidence_hit3": pct("hit3"), "context_evidence_rate": pct("context_hit"),
               "avg_context_chars": round(statistics.mean(t["context_chars"] for t in traces)),
               "median_ms": round(statistics.median(t["elapsed_ms"] for t in traces), 1), "cost_usd": 0}
    return summary, traces


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("dev", "test"), required=True)
    parser.add_argument("--configs", nargs="+",
                        default=["tfidf", "dense", "bm25", "hybrid", "hybrid_rerank", "hybrid_rerank_b2400"])
    parser.add_argument("--locked", action="store_true", help="Xác nhận đã commit chốt cấu hình trước khi chạy test")
    args = parser.parse_args()
    if args.split == "test" and not args.locked:
        raise SystemExit("Chưa được chạy test. Chốt cấu hình trên dev, commit, rồi chạy lại với --locked")

    questions = [q for q in json.loads(QUESTIONS.read_text(encoding="utf-8")) if q["split"] == args.split]
    configs = build_configs(args.configs)
    out = RESULTS / args.split
    out.mkdir(parents=True, exist_ok=True)
    summaries, all_traces = [], []
    for name, (retriever, top_k, budget, hypothesis) in configs.items():
        summary, traces = evaluate(name, retriever, top_k, budget, questions)
        summaries.append({**summary, "hypothesis": hypothesis})
        all_traces += traces

    (out / "summary.json").write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "traces.json").write_text(json.dumps(all_traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["| Cấu hình | Phương pháp, top-k, budget | Hit@1 | Evidence Hit@3 | Context Evidence Rate | ms/câu |",
             "|---|---|---|---|---|---|"]
    lines += [f"| {s['config']} | {s['method']}, k={s['top_k']}, {s['budget_chars']} ký tự | {s['hit1']} | "
              f"{s['evidence_hit3']} | {s['context_evidence_rate']} | {s['median_ms']} |" for s in summaries]
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nKẾT QUẢ RETRIEVAL · {args.split.upper()} · {len(questions)} câu có đáp án\n")
    print("\n".join(lines))
    print("\nCâu trượt Evidence Hit@3 (dùng để phân tích lỗi):")
    for name in configs:
        missed = [t["query_id"] for t in all_traces if t["config"] == name and not t["hit3"]]
        print(f"  {name:<22} {', '.join(missed) or '(không có)'}")
    print(f"\nĐã lưu {out.relative_to(ROOT)}/summary.md, summary.json, traces.json")


if __name__ == "__main__":
    main()