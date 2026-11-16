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
    ("test", "multimodal"): {
        "at01": (True, "35%; chunk Table 2 trang 40 (kèm đoạn văn cùng trang)"),
        "at02": (True, "63, đúng cột THE; Table 3 trang 43"),
        "at03": (True, "6,9%; Table 4 trang 44"),
        "at04": (True, "23 (2010) và 63 (2017); Table 5 trang 50"),
        "at05": (True, "Mongolia + đúng 2 điều kiện (<0,5% GDP, >40%); ô ma trận Table 12 trang 61"),
        "at06": (True, "15% (2030) so với 9% (2017); Table 14 trang 68"),
        "at07": (True, "Enhanced Governance, Effective Financing; Figure 2 trang 34"),
        "at08": (True, "Không tồn tại (ô cam); Figure 11 trang 56"),
        "at09": (True, "Chỉ Accountability/Credibility, không nhầm ô xám Professional certification; Figure 11"),
        "at10": (True, "Đủ 2 mục tiêu (giữ lỗi chính tả 'Buiding' của bản gốc); Figure 14 trang 80"),
        "at11": (True, "Grants for (process) innovation, Loans for innovation (equipment); Figure 14"),
        "at12": (True, "Finland 1,89; Figure ES.3 trang 20"),
        "at13": (True, "Republic of Korea 4,2; Figure 10 trang 51"),
        "at14": (True, "Foreign language skills ≈0,25; Figure 9 trang 45"),
        "at15": (True, "Primary or below và Secondary or below, có số ước lượng; Figure 8 trang 45"),
        "at16": (True, "Primary ≈36% → ≈24% (trong khoảng chấp nhận); Figure 13 trang 67"),
        "at17": (True, "0,4 (Figure 10) > 0,33 (Figure ES.3), kết luận GERD cao hơn; có ghi chú 0,69 đúng theo note của biểu đồ"),
        "at18": (True, "Red River Delta 52%, Kinh/Hoa 45%, chênh 7 điểm; Table 2 + Figure 6 trang 40 (và đoạn trang 39)"),
        "at19": (True, "2 vs 4 (QS) và 183 vs 205 (H-index), 2 kết luận đúng; Table 3 tr. 43 + Table 5 tr. 50"),
        "at20": (True, "55% (2017, Figure 12) và 46% (2018, Table 11); trang 60 (và đoạn trang 59)"),
        "at21": (True, "28% và 14%; đoạn văn trang 56"),
        "at22": (True, "Under US$40 / VND 9 triệu vs close to US$130 / VND 30 triệu; trang 20 và 61"),
        "at23": (True, "Hạng 45 (2018) từ 64 (2008); trang 51"),
        "at24": (True, "1,6%; trang 64"),
        "at25": (True, "Từ chối, không lấy số 2015 thay cho 2020"),
        "at26": (True, "Từ chối, không lấy học phí trung bình chung"),
        "at27": (True, "Từ chối, không lấy số 2018 (33%)"),
        "at28": (True, "Từ chối, không có nhóm 'data science'"),
        "at29": (True, "Từ chối, không lấy số 2016"),
        "at30": (True, "Từ chối, không lấy mục tiêu % SV nước ngoài"),
    },
    ("test", "text_only"): {
        "at01": (True, "35%; text trang 40"),
        "at02": (True, "63; text trang 43"),
        "at03": (True, "6,9%; text trang 44"),
        "at04": (False, "Từ chối sau 3 lần tìm: không đọc được ô Vietnam × Citable documents"),
        "at05": (True, "Mongolia + 2 điều kiện; text trang 61"),
        "at06": (True, "15% vs 9%; text trang 68"),
        "at07": (True, "Đúng 2 trụ cột (trang 34); citation phụ trang 23 chỉ nói chung về khung phân tích"),
        "at08": (False, "Từ chối: text không có thông tin màu ô"),
        "at09": (False, "Từ chối: text không có thông tin màu ô"),
        "at10": (False, "Từ chối"),
        "at11": (True, "Đủ 2 công cụ; text trang 80"),
        "at12": (True, "Finland 1,89; nhãn số có trong text trang 20"),
        "at13": (True, "Korea 4,2; nhãn số có trong text trang 51"),
        "at14": (False, "Từ chối: biểu đồ không nhãn số"),
        "at15": (False, "Từ chối: biểu đồ không nhãn số"),
        "at16": (False, "Từ chối: biểu đồ không nhãn số"),
        "at17": (False, "Từ chối: không ghép được 2 biểu đồ"),
        "at18": (True, "52% vs 45%, chênh 7; text trang 39–40"),
        "at19": (False, "Từ chối: không ghép được 2 bảng"),
        "at20": (True, "55% và 46%; text trang 59–60"),
        "at21": (True, "28% và 14%"),
        "at22": (True, "40 vs 130 USD / 9 vs 30 triệu VND"),
        "at23": (True, "45 và 64"),
        "at24": (True, "1,6%"),
        "at25": (False, "KHÔNG từ chối: lấy GERD 0,4% (năm 2015) trả lời cho năm 2020, còn nói 'không rõ năm' — khẳng định thiếu căn cứ"),
        "at26": (True, "Từ chối đúng"),
        "at27": (True, "Từ chối đúng"),
        "at28": (True, "Từ chối đúng"),
        "at29": (True, "Từ chối đúng"),
        "at30": (True, "Từ chối đúng"),
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
