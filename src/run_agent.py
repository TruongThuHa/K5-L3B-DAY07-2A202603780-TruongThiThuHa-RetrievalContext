"""Bước D3 · Chạy agent thật trên một split và lưu trace đầy đủ cho từng câu.

    python -m src.run_agent --split dev --config selected --only q01      # thử 1 câu
    python -m src.run_agent --split dev --config selected                 # cả dev
    python -m src.run_agent --split dev --config baseline
    python -m src.run_agent --split test --config selected --locked       # CHỈ sau khi commit chốt cấu hình

Agent chỉ đọc data/he2020/cases.json (id, split, câu hỏi, filter) -> không có gold/đáp án trong vòng lặp.
"""
import argparse
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

from .agent import LLMController, make_client
from .retrievers import ROOT, BM25Retriever, DenseRetriever, HybridRetriever, RerankRetriever, load_chunks

sys.path.insert(0, str(ROOT / "starter"))
from agentic import run_agent  # noqa: E402  (vòng lặp agent của đề: giới hạn search, kiểm tra citation có trong context)

CASES = ROOT / "data" / "he2020" / "cases.json"
RESULTS = ROOT / "results" / "agent"

# baseline = dense Day 6 + budget mặc định của đề; selected = cấu hình chọn trên dev (Phần C)
CONFIGS = {
    "baseline": {"retriever": "dense", "top_k": 3, "budget": 800, "max_searches": 3},
    "selected": {"retriever": "hybrid_rerank", "top_k": 3, "budget": 2400, "max_searches": 3},
}


def build_retriever(name: str):
    dense = DenseRetriever()
    if name == "dense":
        return dense
    hybrid = HybridRetriever(dense, BM25Retriever(load_chunks()))
    return RerankRetriever(hybrid) if name == "hybrid_rerank" else hybrid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("dev", "test"), required=True)
    parser.add_argument("--config", choices=sorted(CONFIGS), required=True)
    parser.add_argument("--only", nargs="*", help="Chỉ chạy các câu này (vd: q01 n01) để thử nhanh")
    parser.add_argument("--locked", action="store_true")
    args = parser.parse_args()
    if args.split == "test" and not args.locked:
        raise SystemExit("Chưa được chạy test. Chốt cấu hình trên dev, commit, rồi chạy lại với --locked")

    cfg = CONFIGS[args.config]
    cases = [c for c in json.loads(CASES.read_text(encoding="utf-8")) if c["split"] == args.split]
    if args.only:
        cases = [c for c in cases if c["id"] in args.only]
    client, model = make_client()
    retriever = build_retriever(cfg["retriever"])
    out = RESULTS / args.split / args.config
    out.mkdir(parents=True, exist_ok=True)

    traces = []
    for i, case in enumerate(cases, start=1):
        controller = LLMController(client, model, cfg["max_searches"])
        start = time.perf_counter()
        try:
            result = run_agent(case["question"], controller, retriever, filters=case.get("filter"),
                               max_searches=cfg["max_searches"], top_k=cfg["top_k"], budget=cfg["budget"])
            error = None
        except Exception as exc:   # lỗi model/vector store: ghi riêng, KHÔNG thay bằng câu trả lời giả
            result = {"status": "error", "answer": "", "citations": [], "events": []}
            error = f"{type(exc).__name__}: {exc}"
        searches = [e for e in result["events"] if e["event"] == "search"]
        trace = {"query_id": case["id"], "split": case["split"], "config": args.config, **cfg, "model": model,
                 "question": case["question"], "filter": case.get("filter"), **result, "error": error,
                 "n_searches": len(searches), "llm_calls": controller.calls,
                 "tokens_in": sum(c["tokens_in"] or 0 for c in controller.calls),
                 "tokens_out": sum(c["tokens_out"] or 0 for c in controller.calls),
                 "elapsed_s": round(time.perf_counter() - start, 2)}
        traces.append(trace)
        show = result["answer"][:110].replace("\n", " ")
        print(f"[{i}/{len(cases)}] {case['id']}: {result['status']:<8} searches={len(searches)} "
              f"{trace['elapsed_s']}s | {error or show}")

    name = "traces.json" if not args.only else f"traces_only_{'_'.join(args.only)}.json"
    (out / name).write_text(json.dumps(traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ok = [t for t in traces if t["status"] != "error"]
    print(f"\nModel {model} | {args.config} | {args.split}: {len(traces)} câu, "
          f"answered {sum(t['status'] == 'answered' for t in traces)}, "
          f"abstain {sum(t['status'] == 'abstain' for t in traces)}, error {len(traces) - len(ok)}")
    if ok:
        dist = dict(sorted(Counter(t["n_searches"] for t in ok).items()))
        print(f"Phân bố số lần search {{số lần: số câu}}: {dist} | token vào {sum(t['tokens_in'] for t in ok)}, "
              f"ra {sum(t['tokens_out'] for t in ok)} | trung vị {statistics.median(t['elapsed_s'] for t in ok)}s/câu")
    print(f"Đã lưu {(out / name).relative_to(ROOT)}")


if __name__ == "__main__":
    main()