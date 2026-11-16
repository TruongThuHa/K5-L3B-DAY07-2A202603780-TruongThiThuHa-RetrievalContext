"""Bước B · Lấy dữ liệu Day 6 sang Day 7.

1. Xuất chunk của cấu hình đã chọn ở Day 6 (strategy B) từ pgvector -> data/he2020/chunks.json
2. Chuyển 20 câu benchmark Day 6 sang schema Day 7          -> data/he2020/questions.json
3. Gộp 24 câu (20 có đáp án + 4 thiếu bằng chứng, KHÔNG có gold) -> data/he2020/cases.json

Chạy từ thư mục gốc repo:  python -m src.export_day6
"""
import argparse
import json
import os
import unicodedata
from collections import Counter
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "he2020"
DAY6_QUESTIONS = Path.home() / "Documents" / "K5-L3B-DAY06-2A202603780-DataIngestion" / "benchmark" / "questions.json"


def flatten(text: str) -> str:
    """Giống hàm flatten của Day 6: chuẩn hóa NFC + gộp mọi khoảng trắng thành một dấu cách."""
    return " ".join(unicodedata.normalize("NFC", text).split())


def export_chunks(database_url: str, strategy: str) -> list[dict]:
    """Đọc thẳng bảng chunks của Day 6 (không tạo lại embedding, không đổi nội dung chữ)."""
    with psycopg.connect(database_url, connect_timeout=5) as conn:
        rows = conn.execute(
            """SELECT chunk_id, document_id, source, page, section, text, metadata, embedding_model
               FROM chunks WHERE strategy = %s ORDER BY page, chunk_id""", (strategy,)).fetchall()
    if not rows:
        raise RuntimeError(f"Không có chunk nào với strategy = '{strategy}'. Database Day 6 đã bật chưa?")
    chunks = []
    for chunk_id, document_id, source, page, section, text, metadata, model in rows:
        meta = dict(metadata or {})
        meta.update(section=section, day6_strategy=strategy, embedding_model=model)
        # Text được làm "phẳng" (bỏ xuống dòng) để so khớp evidence giống Day 6; nội dung chữ giữ nguyên.
        chunks.append({"id": chunk_id, "text": flatten(text), "source_id": document_id,
                       "source": source, "page": page, "metadata": meta})
    return chunks


def convert_questions(day6_questions: list[dict], chunks: list[dict]) -> list[dict]:
    """Day 6: gold_page + evidence_quote + alternative_gold  ->  Day 7: gold = [{source_id, page, evidence}]."""
    converted = []
    for q in day6_questions:
        options = [(q["gold_page"], q["evidence_quote"])]
        options += [(a["gold_page"], a["evidence_quote"]) for a in q.get("alternative_gold", [])]
        gold = []
        for page, evidence in options:
            evidence = flatten(evidence)
            if any(c["source_id"] == q["gold_source_id"] and c["page"] == page and evidence in c["text"] for c in chunks):
                gold.append({"source_id": q["gold_source_id"], "page": page, "evidence": evidence})
            else:
                print(f"  CẢNH BÁO {q['id']}: evidence trang {page} không nằm trọn trong một chunk -> bỏ phương án này")
        if not gold:
            raise RuntimeError(f"{q['id']}: không còn evidence nào nằm trọn trong chunk")
        item = {"id": q["id"], "split": q["split"], "type": q["type"], "question": q["question"],
                "expected_answer": q["expected_answer"], "answerable": True, "gold": gold}
        if q.get("filter"):
            item["filter"] = q["filter"]
        converted.append(item)
    return converted


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Xuất dữ liệu Day 6 sang Day 7")
    parser.add_argument("--day6-questions", type=Path, default=DAY6_QUESTIONS)
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")

    chunks = export_chunks(os.environ["DATABASE_URL"], os.getenv("DAY6_STRATEGY", "B"))
    questions = convert_questions(json.loads(args.day6_questions.read_text(encoding="utf-8")), chunks)
    unanswerable = json.loads((OUT / "unanswerable.json").read_text(encoding="utf-8"))
    # cases.json là thứ duy nhất agent được đọc: chỉ có id, split, câu hỏi, filter; không có đáp án/gold.
    cases = [{k: q[k] for k in ("id", "split", "question", "answerable") if k in q} | (
             {"filter": q["filter"]} if q.get("filter") else {}) for q in questions + unanswerable]

    write_json(OUT / "chunks.json", chunks)
    write_json(OUT / "questions.json", questions)
    write_json(OUT / "cases.json", cases)

    print(f"Chunk: {len(chunks)} | trang: {len({c['page'] for c in chunks})} | "
          f"section: {dict(Counter(c['metadata']['section'] for c in chunks))}")
    for split in ("dev", "test"):
        yes = sum(c["split"] == split and c["answerable"] for c in cases)
        no = sum(c["split"] == split and not c["answerable"] for c in cases)
        print(f"{split}: {yes} câu có đáp án + {no} câu thiếu bằng chứng")
    print("Đã ghi data/he2020/chunks.json, questions.json, cases.json")


if __name__ == "__main__":
    main()