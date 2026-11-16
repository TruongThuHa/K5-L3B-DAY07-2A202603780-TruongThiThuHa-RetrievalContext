"""Thử thách nâng cao · Bước 2: biến kết quả trích bảng/biểu đồ/sơ đồ thành chunk, embed và lưu vào pgvector.

    python -m src.adv_index

- Mỗi phần tử trực quan -> 1 chunk id `he2020-pNNN-VKK`, text = "[Table 7: tiêu đề] (page N, table)\\n<nội dung>",
  metadata giữ kind, label, title, vùng trang box_2d (0-1000) và đường dẫn ảnh trang để kiểm chứng.
- Embed bằng đúng model Day 6 (bge-small-en-v1.5, 384 chiều), lưu vào bảng `chunks` với strategy = 'V'
  (chunk chữ Day 6 vẫn là strategy 'B'; retrieval nâng cao tìm trên cả 'B,V').
- Ghi data/advanced/visual_chunks.json, data/advanced/chunks_all.json (B + V) và results/advanced/index_stats.json.
"""
import json
import os
import time
from collections import Counter
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from .export_day6 import flatten
from .retrievers import EMBED_MODEL

ROOT = Path(__file__).resolve().parents[1]
ADV = ROOT / "data" / "advanced"
TEXT_CHUNKS = ROOT / "data" / "he2020" / "chunks.json"
STRATEGY = "V"


def build_visual_chunks(text_chunks: list[dict]) -> tuple[list[dict], list[dict]]:
    section = {c["page"]: c["metadata"].get("section") for c in text_chunks}
    source = text_chunks[0]["source"]
    chunks, raws = [], []
    for path in sorted((ADV / "visual_raw").glob("p*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        raws.append(raw)
        page = raw["page"]
        for k, el in enumerate(raw["elements"]):
            kind, label = str(el.get("kind", "")).lower(), str(el.get("label", "")).strip()
            title, content = str(el.get("title", "")).strip(), str(el.get("content", "")).strip()
            if not content:
                continue
            head = f"[{label + ': ' if label else ''}{title}] (page {page}, {kind})"
            chunks.append({"id": f"he2020-p{page:03d}-V{k:02d}", "text": head + "\n" + content,
                           "source_id": "he2020", "source": source, "page": page,
                           "metadata": {"section": section.get(page), "kind": kind, "label": label, "title": title,
                                        "box_2d": el.get("box_2d"), "page_image": f"data/advanced/pages/p{page:03d}.png",
                                        "extractor": raw.get("model"), "day6_strategy": STRATEGY}})
    return chunks, raws


def main() -> None:
    from sentence_transformers import SentenceTransformer

    load_dotenv(ROOT / ".env")
    text_chunks = json.loads(TEXT_CHUNKS.read_text(encoding="utf-8"))
    visual, raws = build_visual_chunks(text_chunks)
    if not visual:
        raise SystemExit("Chưa có kết quả trích trong data/advanced/visual_raw/. Chạy src.adv_extract_visual trước.")

    start = time.perf_counter()
    model = SentenceTransformer(EMBED_MODEL)
    # Document KHÔNG thêm tiền tố truy vấn (giống cách Day 6 embed chunk chữ)
    vectors = model.encode([flatten(c["text"]) for c in visual], batch_size=16, normalize_embeddings=True)
    rows = [(STRATEGY, c["id"], c["source_id"], c["source"], c["page"], c["metadata"]["section"], c["text"],
             json.dumps(c["metadata"], ensure_ascii=False), EMBED_MODEL, "[" + ",".join(f"{v:.7f}" for v in vec) + "]")
            for c, vec in zip(visual, vectors)]
    with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO chunks (strategy, chunk_id, document_id, source, page, section, text, metadata,
                                    embedding_model, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (strategy, chunk_id) DO UPDATE SET text = EXCLUDED.text, metadata = EXCLUDED.metadata,
                    page = EXCLUDED.page, section = EXCLUDED.section, embedding_model = EXCLUDED.embedding_model,
                    embedding = EXCLUDED.embedding""", rows)
            cur.execute("DELETE FROM chunks WHERE strategy = %s AND NOT (chunk_id = ANY(%s))",
                        (STRATEGY, [c["id"] for c in visual]))
            in_db = cur.execute("SELECT count(*) FROM chunks WHERE strategy = %s", (STRATEGY,)).fetchone()[0]
    seconds = round(time.perf_counter() - start, 1)

    # Chunk dùng cho BM25/agent: text chữ Day 6 + chunk trực quan (giữ xuống dòng để bảng Markdown còn đủ hàng/cột)
    all_chunks = text_chunks + visual
    (ADV / "visual_chunks.json").write_text(json.dumps(visual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ADV / "chunks_all.json").write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pages_with_visual = sorted({c["page"] for c in visual})
    stats = {"document": "he2020.pdf (World Bank 2020, 102 trang PDF)", "content_pages_indexed": len({c["page"] for c in text_chunks}),
             "pages_sent_to_vision": len(raws), "pages_with_visual_elements": len(pages_with_visual),
             "visual_chunks": len(visual), "by_kind": dict(Counter(c["metadata"]["kind"] for c in visual)),
             "text_chunks": len(text_chunks), "total_chunks": len(all_chunks), "rows_in_db_strategy_V": in_db,
             "embedding_model": EMBED_MODEL, "dimensions": int(vectors.shape[1]), "embed_and_store_seconds": seconds,
             "vision_model": sorted({r.get("model") for r in raws}),
             "vision_tokens_in": sum(r.get("tokens_in") or 0 for r in raws),
             "vision_tokens_out": sum(r.get("tokens_out") or 0 for r in raws),
             "vision_seconds_total": round(sum(r.get("seconds") or 0 for r in raws), 1)}
    out = ROOT / "results" / "advanced"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
