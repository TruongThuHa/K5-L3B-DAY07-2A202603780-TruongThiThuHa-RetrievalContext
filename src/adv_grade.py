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
LABELS: dict[tuple[str, str], dict[str, tuple[bool, str]]] = {
    ("dev", "multimodal"): {
        "ad01": (True, "76, đúng cột QS; trích chunk Table 3 trang 43"),
        "ad02": (True, "0,24 đúng hàng % HE/GDP cột 2011; chunk Table 9 trang 58"),
        "ad03": (True, "65.628 đúng ô Universities × Researchers; chunk Table 13 trang 62"),
        "ad04": (True, "Nêu đủ Competitive research grants (Yes/partially) và Centers of excellence (Partially); Table 17 trang 79"),
        "ad05": (True, "Đủ 3 HE outcomes; chunk Figure 2 trang 34"),
        "ad06": (True, "Đủ 4 đơn vị đánh giá; chunk Figure 11 trang 56"),
        "ad07": (True, "Đủ 3 chức năng (giữ lỗi chính tả 'adotion' của bản gốc, có ghi adoption); Figure 14 trang 80"),
        "ad08": (True, "Rep. of Korea và Singapore = 1,00; Figure ES.3 trang 20"),
        "ad09": (True, "3,4; Figure 10 trang 51"),
        "ad10": (True, "Female - Male ≈13; Figure 7 trang 41"),
        "ad11": (False, "Sai: nói không nước nào vượt 100% vì vision đọc đỉnh Hàn Quốc ≈100 (gốc ≈104); câu trả lời còn lộ JSON tool call"),
        "ad12": (True, "0,6 (Figure 10 tr. 51) và 3,16 (Table 5 tr. 50), trích đúng 2 chunk"),
        "ad13": (True, "1.276.647 = 3.584.647 − 2.308.000, nêu đủ 2 số; Table 14 tr. 68 + Table 1 tr. 38"),
        "ad14": (True, "More than 600 GRIs; đoạn văn trang 51"),
        "ad15": (True, "US$1.124 triệu; chú thích trang 60"),
        "ad16": (True, "Từ chối, không lấy nhầm tỷ lệ toàn hệ thống (23) thành của VNU-Hanoi"),
        "ad17": (True, "Từ chối, không bịa hạng 2023"),
        "ad18": (True, "Từ chối, không bịa số chi"),
    },
    ("dev", "text_only"): {
        "ad01": (True, "76; text trang 43 có bảng dạng chữ"),
        "ad02": (True, "0,24; text trang 58"),
        "ad03": (False, "Từ chối sau 3 lần tìm: không đưa được ô Universities × Researchers (Table 13) vào context"),
        "ad04": (False, "Chỉ nêu 1/2 modality (thiếu Centers of excellence)"),
        "ad05": (True, "Đủ 3 HE outcomes (chữ trong sơ đồ có trong text pypdf)"),
        "ad06": (False, "Từ chối sau 3 lần tìm: text pypdf của sơ đồ Figure 11 không đủ để agent xác định hàng tiêu đề"),
        "ad07": (True, "Đủ 3 chức năng; text trang 80 có chữ trong sơ đồ"),
        "ad08": (True, "Đúng 2 nước; nhãn số biểu đồ có trong text trang 20"),
        "ad09": (True, "3,4; nhãn số có trong text trang 51"),
        "ad10": (False, "Từ chối: biểu đồ không nhãn số, text không có giá trị"),
        "ad11": (False, "Từ chối: biểu đồ đường không có nhãn số"),
        "ad12": (False, "Nội dung đúng nhưng câu trả lời lộ JSON tool call (lỗi định dạng), không chấm đạt"),
        "ad13": (False, "Từ chối sau 3 lần tìm: không có đủ cả hai tổng (Table 14 và Table 1) trong context"),
        "ad14": (False, "Sai: 'several hundred' thay vì 'more than 600', trích trang 18 không có số này"),
        "ad15": (True, "US$1.124 triệu"),
        "ad16": (True, "Từ chối đúng"),
        "ad17": (True, "Từ chối đúng"),
        "ad18": (True, "Từ chối đúng"),
    },
}


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
