"""Bước E1 · Nhãn chấm tay cho câu trả lời của agent -> reviews.json + bảng đọc lại review_sheet.md

    python -m src.make_reviews --split dev

Nhãn được soạn sau khi ĐỌC từng câu trả lời và từng đoạn được trích (không dựa vào việc ID hợp lệ).
Cách chấm theo BENCHMARK.md:
    answer_grade      : 0 = sai/thiếu evidence/từ chối câu có đáp án; 1 = đúng một phần; 2 = đúng và đủ
    citation_support  : mỗi citation một True/False = đoạn đó có thật sự hỗ trợ câu trả lời không
    abstention_correct: câu thiếu bằng chứng -> agent có từ chối và không thêm khẳng định vô căn cứ không
Đáp án chuẩn chỉ dùng ở bước chấm này, không bao giờ đưa vào agent.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "data" / "he2020" / "questions.json"
CASES = ROOT / "data" / "he2020" / "cases.json"
CHUNKS = ROOT / "data" / "he2020" / "chunks.json"

# (split, config) -> query_id -> (answer_grade | None, [citation_support...], abstention_correct | None, lý do)
LABELS = {
    ("dev", "selected"): {
        "q01": (2, [True], None, "54% của 2,3 triệu SV; trang 15 nêu nguyên văn"),
        "q02": (2, [True, True], None, "Hạng 48/157, cao nhất nhóm thu nhập trung bình; cả 2 đoạn đều nêu"),
        "q03": (2, [True], None, "47% (2007) -> 72% (2015); trang 53 nêu nguyên văn"),
        "q04": (2, [True], None, "23/171 trường công thí điểm tự chủ; trang 57"),
        "q05": (2, [True, True], None, "Đủ 5 nước; câu thêm về H-index cũng có trong trang 17"),
        "q06": (2, [True, True], None, "US$574 và 46%; câu văn trang 59 + bảng 11 trang 60"),
        "q07": (2, [True], None, "Decision 37 (2013), 4,5 -> 2,2 triệu; trang 38"),
        "q08": (2, [True, True], None, "MOET quản lý ĐH, MOLISA quản lý cao đẳng TVET; trang 18 và 53"),
        "q09": (2, [True], None, "Cao hơn 93% so với tốt nghiệp THPT; trang 44"),
        "q10": (2, [True], None, "1959–1960; Box 5 trang 65"),
        "q11": (2, [True], None, "SV thu nhập dưới trung bình được miễn trả; trang 91"),
        "q12": (2, [True], None, "Tổng 3,6 triệu (thêm 1,3 triệu); trang 68, đúng filter policy_options"),
        "q13": (2, [True], None, "US$316 (15% GDP/người) năm 2015; trang 59"),
        "q14": (0, [], None, "Từ chối nhầm: evidence nằm trong BẢNG trang 75 (chunk p075-B01); retrieval chỉ lấy được p075-B00 (lỗi dev #2)"),
        "q15": (2, [True], None, "Khoảng 15 năm; trang 85"),
        "n01": (None, [], True, "Tìm 3 lần (dropout/completion/attrition), không thấy, từ chối đúng"),
        "n02": (None, [], True, "Tìm 3 lần, không có tỷ lệ SV/giảng viên, từ chối đúng"),
    },
    ("dev", "baseline"): {
        "q01": (0, [], None, "Từ chối nhầm: dense có tìm thấy p040-B02 và p015-B00 nhưng budget 800 loại cả hai, chỉ giữ đoạn ngắn p013-B05"),
        "q02": (2, [True], None, "Hạng 48/157 năm 2018, cao nhất nhóm thu nhập trung bình; trang 32"),
        "q03": (0, [], None, "Từ chối nhầm: dense không đưa trang 53/15 vào context"),
        "q04": (0, [], None, "Từ chối nhầm: p057-B00 đứng hạng 1 nhưng bị budget 800 loại, context chỉ còn p057-B03"),
        "q05": (2, [True], None, "Đủ 5 nước; trang 17"),
        "q06": (2, [True], None, "US$574 và 46%; bảng 11 trang 60"),
        "q07": (2, [True], None, "Decision 37 (2013), 4,5 -> 2,2 triệu; trang 38"),
        "q08": (2, [True], None, "MOET và MOLISA; trang 18 nêu đủ"),
        "q09": (2, [True], None, "Cao hơn 93%; trang 44"),
        "q10": (2, [True], None, "1959–1960; trang 65"),
        "q11": (2, [True], None, "Miễn trả cho SV thu nhập dưới trung bình; trang 91"),
        "q12": (0, [], None, "Từ chối nhầm: dense không lấy được đoạn chứa 3,6 triệu (p068-B00) trong cả 3 lần tìm"),
        "q13": (2, [True], None, "US$316 (15% GDP/người); trang 59"),
        "q14": (0, [], None, "Từ chối nhầm: evidence nằm trong bảng trang 75 (p075-B01), chỉ tìm được p075-B00"),
        "q15": (0, [], None, "Từ chối nhầm: p085-B00 có trong top-3 nhưng budget 800 chỉ giữ p055-B01"),
        "n01": (None, [], True, "Từ chối đúng"),
        "n02": (None, [], True, "Từ chối đúng"),
    },
    ("test", "selected"): {
        "q16": (2, [True], None, "Khoảng 93%; trang 31 nêu nguyên văn"),
        "q17": (2, [True, True], None, "Đứng cuối bảng theo H-index; trang 50 và trang 17 đều nêu"),
        "q18": (2, [True, True], None, "Từ 0,23% lên ít nhất 0,8% GDP năm 2030; trang 23 và 26, đúng filter executive_summary"),
        "q19": (2, [True, True], None, "Chương trình cho vay SLP do VSPB quản lý; trang 20 và 64"),
        "q20": (2, [True, True, True], None, "Chênh 34 điểm % (45% so với 11%, 2018); trang 16, 39, 40"),
        "n03": (None, [], True, "Tìm 3 lần, tài liệu chỉ nói đóng cửa kéo dài, không có số tuần; từ chối đúng"),
        "n04": (None, [], True, "Tìm 3 lần, không có lương giảng viên; không lấy nhầm thu nhập người tốt nghiệp; từ chối đúng"),
    },
    ("test", "baseline"): {
        "q16": (2, [True], None, "Khoảng 93%; trang 31"),
        "q17": (2, [True], None, "Thấp hơn tất cả các nước so sánh theo H-index; trang 17"),
        "q18": (0, [], None, "Từ chối nhầm: dense tìm thấy p023-B00 ở hạng 1 nhưng budget 800 chỉ giữ p021-B00"),
        "q19": (2, [True], None, "SLP do VSPB quản lý; trang 64"),
        "q20": (2, [True], None, "Chênh 34 điểm %; trang 16 (không nêu 45%/11% nhưng câu hỏi chỉ hỏi độ chênh)"),
        "n03": (None, [], True, "Từ chối đúng"),
        "n04": (None, [], True, "Từ chối đúng"),
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("dev", "test"), required=True)
    args = parser.parse_args()
    gold = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}
    cases = {c["id"]: c for c in json.loads(CASES.read_text(encoding="utf-8")) if c["split"] == args.split}
    chunks = {c["id"]: c for c in json.loads(CHUNKS.read_text(encoding="utf-8"))}
    sheet = [f"# Bảng chấm tay agent · {args.split}\n",
             "Nhãn soạn sau khi đọc từng câu trả lời và từng đoạn được trích (có AI hỗ trợ đọc), "
             "học viên đọc lại và xác nhận. Đáp án chuẩn chỉ dùng để chấm, không đưa vào agent.\n"]
    for (split, config), labels in LABELS.items():
        if split != args.split:
            continue
        folder = ROOT / "results" / "agent" / split / config
        traces = {t["query_id"]: t for t in json.loads((folder / "traces.json").read_text(encoding="utf-8"))}
        missing = set(cases) - set(labels)
        if missing:
            raise SystemExit(f"{config}: còn thiếu nhãn cho {sorted(missing)}")
        reviews = []
        sheet.append(f"\n## Cấu hình `{config}`\n")
        for qid in sorted(cases, key=lambda i: (i[0] == "n", i)):
            grade, support, abstain_ok, reason = labels[qid]
            t = traces[qid]
            if t["status"] == "error":
                continue
            if len(support) != len(t["citations"]):
                raise SystemExit(f"{config}/{qid}: trace có {len(t['citations'])} citation nhưng nhãn có {len(support)}")
            if grade is not None and t["status"] == "abstain" and grade != 0:
                raise SystemExit(f"{config}/{qid}: từ chối câu có đáp án phải chấm 0")
            item = {"query_id": qid, "citation_support": support, "reason": reason}
            item |= {"answer_grade": grade} if grade is not None else {"abstention_correct": abstain_ok}
            reviews.append(item)
            expected = gold[qid]["expected_answer"] if qid in gold else "(không có trong tài liệu -> phải từ chối)"
            label = f"answer_grade={grade}" if grade is not None else f"abstention_correct={abstain_ok}"
            sheet.append(f"### {qid} · {t['status']} · {t['n_searches']} lần search · **{label}**\n")
            sheet.append(f"- Câu hỏi: {t['question']}\n- Đáp án chuẩn: {expected}\n- Agent: {t['answer']}")
            for cid, ok in zip(t["citations"], support):
                c = chunks[cid]
                sheet.append(f"- Trích `{cid}` (trang {c['page']}) hỗ trợ: {'✅' if ok else '❌'} — “{c['text'][:220]}…”")
            sheet.append(f"- Lý do: {reason}\n")
        (folder / "reviews.json").write_text(json.dumps(reviews, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Đã ghi {(folder / 'reviews.json').relative_to(ROOT)} ({len(reviews)} nhãn)")
    out = ROOT / "results" / "agent" / args.split / "review_sheet.md"
    out.write_text("\n".join(sheet) + "\n", encoding="utf-8")
    print(f"Đã ghi {out.relative_to(ROOT)} -> mở file này để đọc lại từng nhãn")


if __name__ == "__main__":
    main()