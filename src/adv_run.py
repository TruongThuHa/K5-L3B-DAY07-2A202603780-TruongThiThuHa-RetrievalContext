"""Thử thách nâng cao · Bước 3: chạy agent trên benchmark tài liệu có bảng/biểu đồ/sơ đồ.

    python -m src.adv_run --split dev --config text_only
    python -m src.adv_run --split dev --config multimodal
    python -m src.adv_run --split test --config multimodal --locked     # CHỈ sau khi commit chốt cấu hình

Agent chỉ nhận câu hỏi (data/advanced/cases.json); đáp án/evidence (questions.json) chỉ dùng khi chấm.
"""
import argparse
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

from .agent import SYSTEM_PROMPT, LLMController, make_client
from .retrievers import ROOT, BM25Retriever, DenseRetriever, HybridRetriever, RerankRetriever, load_chunks

sys.path.insert(0, str(ROOT / "starter"))
from agentic import run_agent  # noqa: E402

CASES = ROOT / "data" / "advanced" / "cases.json"
ALL_CHUNKS = ROOT / "data" / "advanced" / "chunks_all.json"
RESULTS = ROOT / "results" / "advanced"

ADV_PROMPT = SYSTEM_PROMPT + """
6. The document also contains tables, charts and diagrams. They were transcribed into passages whose id ends in
   -Vxx and whose first line gives the label, e.g. "[Table 5: ...] (page 50, table)". When a question names a
   table or figure, search with its label and the row/column/series names. Read table cells by matching BOTH the
   row and the column header; for charts use the stated data labels/values; for diagrams use the colour legend.
7. For questions with several parts, make sure every part is supported; search separately for a missing part.
8. You may do simple arithmetic (difference, sum) on cited numbers; show the numbers you used."""

CONFIGS = {
    # = cấu hình đã chốt của phần cơ bản: chỉ chunk chữ Day 6
    "text_only": {"strategies": "B", "chunks": "text", "top_k": 3, "budget": 2400, "max_searches": 3, "depth": 20},
    # thêm chunk bảng/biểu đồ/sơ đồ (strategy V), context rộng hơn vì bảng dài
    "multimodal": {"strategies": "B,V", "chunks": "all", "top_k": 4, "budget": 6000, "max_searches": 4, "depth": 30},
}


def build_retriever(cfg: dict):
    chunks = load_chunks(ALL_CHUNKS) if cfg["chunks"] == "all" else load_chunks()
    dense = DenseRetriever(strategy=cfg["strategies"], chunks=chunks)
    hybrid = HybridRetriever(dense, BM25Retriever(chunks), depth=cfg["depth"])
    return RerankRetriever(hybrid, depth=cfg["depth"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("dev", "test"), required=True)
    parser.add_argument("--config", choices=sorted(CONFIGS), required=True)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--locked", action="store_true")
    args = parser.parse_args()
    if args.split == "test" and not args.locked:
        raise SystemExit("Chưa được chạy test. Chốt cấu hình trên dev, commit, rồi chạy lại với --locked")

    cfg = CONFIGS[args.config]
    cases = [c for c in json.loads(CASES.read_text(encoding="utf-8")) if c["split"] == args.split]
    if args.only:
        cases = [c for c in cases if c["id"] in args.only]
    client, model = make_client()
    retriever = build_retriever(cfg)
    out = RESULTS / args.split / args.config
    out.mkdir(parents=True, exist_ok=True)

    traces = []
    for i, case in enumerate(cases, start=1):
        controller = LLMController(client, model, cfg["max_searches"], system_prompt=ADV_PROMPT)
        start = time.perf_counter()
        try:
            result = run_agent(case["question"], controller, retriever, filters=None,
                               max_searches=cfg["max_searches"], top_k=cfg["top_k"], budget=cfg["budget"])
            error = None
        except Exception as exc:   # lỗi hệ thống: ghi riêng và tính KHÔNG ĐẠT, không thay bằng kết quả giả
            result = {"status": "error", "answer": "", "citations": [], "events": []}
            error = f"{type(exc).__name__}: {exc}"
        searches = [e for e in result["events"] if e["event"] == "search"]
        trace = {"query_id": case["id"], "split": case["split"], "group": case["group"], "config": args.config,
                 **cfg, "model": model, "question": case["question"], **result, "error": error,
                 "n_searches": len(searches), "llm_calls": controller.calls,
                 "tokens_in": sum(c["tokens_in"] or 0 for c in controller.calls),
                 "tokens_out": sum(c["tokens_out"] or 0 for c in controller.calls),
                 "elapsed_s": round(time.perf_counter() - start, 2)}
        traces.append(trace)
        show = result["answer"][:120].replace("\n", " ")
        print(f"[{i}/{len(cases)}] {case['id']} ({case['group']}): {result['status']:<8} s={len(searches)} "
              f"{trace['elapsed_s']}s | {error or show}", flush=True)

    name = "traces.json" if not args.only else f"traces_only_{'_'.join(args.only)}.json"
    (out / name).write_text(json.dumps(traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ok = [t for t in traces if t["status"] != "error"]
    print(f"\n{model} | {args.config} | {args.split}: {len(traces)} câu, answered "
          f"{sum(t['status'] == 'answered' for t in traces)}, abstain {sum(t['status'] == 'abstain' for t in traces)}, "
          f"error {len(traces) - len(ok)}")
    if ok:
        print(f"search {dict(sorted(Counter(t['n_searches'] for t in ok).items()))} | token vào "
              f"{sum(t['tokens_in'] for t in ok)}, ra {sum(t['tokens_out'] for t in ok)} | trung vị "
              f"{statistics.median(t['elapsed_s'] for t in ok)}s/câu")
    print(f"Đã lưu {(out / name).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
