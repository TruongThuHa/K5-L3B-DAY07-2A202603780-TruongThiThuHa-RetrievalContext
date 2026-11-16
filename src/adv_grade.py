"""Thử thách nâng cao · Bước 4: chấm ĐẠT / KHÔNG ĐẠT từng câu và tổng hợp theo nhóm.

    python -m src.adv_grade --split dev --config multimodal
    python -m src.adv_grade --split test --config multimodal

Theo ADVANCED.md:
- Câu có đáp án ĐẠT khi trả lời đúng và đủ (đúng đơn vị/điều kiện/phép tính), citation chỉ ra đúng trang và vùng
  evidence (chunk bảng/biểu đồ/sơ đồ hoặc đoạn văn của trang đó) và evidence hỗ trợ toàn bộ câu trả lời.
  Đúng một phần, sai citation hoặc từ chối đều KHÔNG ĐẠT.
- Câu thiếu bằng chứng ĐẠT khi từ chối, không thêm khẳng định thiếu căn cứ.
- Lỗi hệ thống / timeout = KHÔNG ĐẠT, vẫn nằm trong mẫu số.
Nhãn được soạn sau khi đọc câu trả lời, từng chunk được trích và đối chiếu ảnh trang gốc (data/advanced/pages/).
"""
import argparse
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "data" / "advanced" / "questions.json"
ALL_CHUNKS = ROOT / "data" / "advanced" / "chunks_all.json"
GROUPS = ["table", "image", "chart", "multihop", "text", "unanswerable"]

# (split, config) -> query_id -> (đạt?, lý do)
LABELS: dict[tuple[str, str], dict[str, tuple[bool, str]]] = {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("dev", "test"), required=True)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    questions = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8")) if q["split"] == args.split}
    chunks = {c["id"]: c for c in json.loads(ALL_CHUNKS.read_text(encoding="utf-8"))}
    folder = ROOT / "results" / "advanced" / args.split / args.config
    traces = {t["query_id"]: t for t in json.loads((folder / "traces.json").read_text(encoding="utf-8"))}
    labels = LABELS.get((args.split, args.config))
    if labels is None or set(labels) != set(questions):
        missing = sorted(set(questions) - set(labels or {}))
        raise SystemExit(f"Chưa đủ nhãn cho {args.split}/{args.config}: thiếu {missing}")

    grades, sheet = [], [f"# Chấm thử thách nâng cao · {args.split} · {args.config}\n"]
    for qid in sorted(questions, key=lambda i: (GROUPS.index(questions[i]["group"]), i)):
        q, t = questions[qid], traces[qid]
        passed, reason = labels[qid]
        if t["status"] == "error" and passed:
            raise SystemExit(f"{qid}: lỗi hệ thống không được chấm đạt")
        if q["answerable"] and t["status"] != "answered" and passed:
            raise SystemExit(f"{qid}: từ chối câu có đáp án không được chấm đạt")
        if not q["answerable"] and t["status"] != "abstain" and passed:
            raise SystemExit(f"{qid}: câu thiếu bằng chứng chỉ đạt khi từ chối")
        grades.append({"query_id": qid, "group": q["group"], "status": t["status"], "pass": passed, "reason": reason,
                       "citations": t["citations"], "n_searches": t["n_searches"], "elapsed_s": t["elapsed_s"],
                       "error": t.get("error")})
        expected = q.get("expected_answer") or "(không có trong tài liệu -> phải từ chối)"
        gold = "; ".join(f"tr. {e['page']} · {e['element']} · {e['region']}" for e in q.get("evidence", [])) or q.get("absence_check")
        sheet.append(f"## {qid} · {q['group']} · {'✅ ĐẠT' if passed else '❌ KHÔNG ĐẠT'}\n")
        sheet.append(f"- Câu hỏi: {q['question']}\n- Đáp án chuẩn: {expected}\n- Tiêu chí: {q.get('accept', 'từ chối, không bịa')}"
                     f"\n- Evidence gốc: {gold}\n- Agent ({t['status']}, {t['n_searches']} lần search): {t['answer']}")
        for cid in t["citations"]:
            c = chunks.get(cid, {})
            sheet.append(f"- Trích `{cid}` (trang {c.get('page')}): “{c.get('text', '')[:260]}…”")
        sheet.append(f"- Lý do: {reason}\n")

    rows, lines = {}, ["| Nhóm test | Đạt / tổng | Tỷ lệ | Lỗi hệ thống |", "|---|---|---|---|"]
    for g in GROUPS:
        sub = [x for x in grades if x["group"] == g]
        if sub:
            n = sum(x["pass"] for x in sub)
            rows[g] = {"pass": n, "total": len(sub)}
            lines.append(f"| {g} | {n}/{len(sub)} | {100 * n / len(sub):.0f}% | {sum(x['status'] == 'error' for x in sub)} |")
    total = sum(x["pass"] for x in grades)
    lines.append(f"| **Toàn bộ** | **{total}/{len(grades)}** | **{100 * total / len(grades):.1f}%** | "
                 f"{sum(x['status'] == 'error' for x in grades)} |")
    tr = list(traces.values())
    summary = {"split": args.split, "config": args.config, "pass": total, "total": len(grades),
               "pass_rate": round(total / len(grades), 4), "threshold_90": total >= 0.9 * len(grades), "by_group": rows,
               "system_errors": sum(x["status"] == "error" for x in grades),
               "median_seconds": statistics.median(t["elapsed_s"] for t in tr),
               "tokens_in": sum(t["tokens_in"] for t in tr), "tokens_out": sum(t["tokens_out"] for t in tr)}
    (folder / "grades.json").write_text(json.dumps({"summary": summary, "grades": grades}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folder / "grade_sheet.md").write_text("\n".join(sheet + ["\n## Tổng hợp\n"] + lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nĐạt ngưỡng 90%: {'CÓ' if summary['threshold_90'] else 'CHƯA'} | trung vị {summary['median_seconds']}s/câu | "
          f"token vào {summary['tokens_in']}, ra {summary['tokens_out']}")
    print(f"Đã ghi {(folder / 'grades.json').relative_to(ROOT)} và grade_sheet.md")


if __name__ == "__main__":
    main()
