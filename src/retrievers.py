"""Bước C · Các phương pháp retrieval.

Mọi retriever có cùng hàm search(query, filters=..., top_k=...) và trả cùng một định dạng:
    {id, text, source_id, source, page, metadata, score, rank, method}
nên agent và script đánh giá dùng chung được.

    1. DenseRetriever   : embedding câu hỏi bằng bge-small-en-v1.5 (giống Day 6) -> pgvector cosine
    2. BM25Retriever    : tìm theo từ khóa (BM25) trên data/he2020/chunks.json
    3. HybridRetriever  : trộn thứ hạng dense + BM25 bằng Reciprocal Rank Fusion (RRF)
    +  RerankRetriever  : lấy nhiều ứng viên rồi cho cross-encoder xếp hạng lại (cấu hình cải thiện)
"""
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = ROOT / "data" / "he2020" / "chunks.json"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"          # PHẢI giống model đã tạo index ở Day 6
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "  # giống Day 6
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
FILTER_COLUMNS = {"section": "section", "page": "page", "source_id": "document_id"}


def load_chunks(path: Path = CHUNKS_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def field(chunk: dict[str, Any], key: str) -> Any:
    """Đọc trường lọc: page/source_id nằm ở ngoài, section nằm trong metadata."""
    return chunk[key] if key in chunk else chunk["metadata"].get(key)


def check_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
    filters = filters or {}
    bad = set(filters) - set(FILTER_COLUMNS)
    if bad:
        raise ValueError(f"Không cho phép lọc theo {sorted(bad)}; chỉ được {sorted(FILTER_COLUMNS)}")
    return filters


def ranked(items: list[dict[str, Any]], method: str) -> list[dict[str, Any]]:
    return [{**item, "rank": i, "method": method} for i, item in enumerate(items, start=1)]


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold())


class DenseRetriever:
    """Phương pháp 1 (bắt buộc): dense retrieval trên vector store Day 6."""
    method = "dense"

    def __init__(self, database_url: str | None = None, strategy: str | None = None,
                 chunks: list[dict[str, Any]] | None = None) -> None:
        from sentence_transformers import SentenceTransformer

        load_dotenv(ROOT / ".env")
        self.url = database_url or os.environ["DATABASE_URL"]
        # "B" = chunk chữ của Day 6; "B,V" = thêm chunk bảng/hình của thử thách nâng cao
        self.strategies = [s.strip() for s in (strategy or os.getenv("DAY6_STRATEGY", "B")).split(",") if s.strip()]
        self.model = SentenceTransformer(EMBED_MODEL)
        self.dimensions = self.model.get_embedding_dimension()
        self.by_id = {c["id"]: c for c in (chunks or load_chunks())}
        with psycopg.connect(self.url, connect_timeout=5) as conn:
            for name in self.strategies:
                row = conn.execute("SELECT vector_dims(embedding), embedding_model FROM chunks WHERE strategy = %s LIMIT 1",
                                   (name,)).fetchone()
                if row is None:
                    raise RuntimeError(f"Database không có chunk strategy '{name}'. Docker đã bật / đã index chưa?")
                if row[0] != self.dimensions or row[1] != EMBED_MODEL:
                    raise RuntimeError(f"Index '{name}' dùng {row[1]} ({row[0]} chiều), query dùng {EMBED_MODEL} "
                                       f"({self.dimensions} chiều): không tương thích")

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        filters = check_filters(filters)
        vector = self.model.encode([QUERY_PREFIX + query], normalize_embeddings=True)[0]
        qv = "[" + ",".join(f"{v:.7f}" for v in vector) + "]"
        where, params = ["strategy = ANY(%s)"], [self.strategies]
        for key, value in filters.items():
            where.append(f"{FILTER_COLUMNS[key]} = %s")
            params.append(value)
        sql = f"""SELECT chunk_id, 1 - (embedding <=> %s::vector) AS score FROM chunks
                  WHERE {' AND '.join(where)} ORDER BY embedding <=> %s::vector LIMIT %s"""
        with psycopg.connect(self.url, connect_timeout=5) as conn:
            rows = conn.execute(sql, [qv, *params, qv, top_k]).fetchall()
        return ranked([{**self.by_id[cid], "score": round(float(score), 4)} for cid, score in rows], self.method)


class BM25Retriever:
    """Phương pháp 2: lexical retrieval bằng BM25 (khớp từ khóa, mạnh với số liệu, tên riêng)."""
    method = "bm25"

    def __init__(self, chunks: list[dict[str, Any]] | None = None) -> None:
        self.chunks = chunks or load_chunks()
        self.index = BM25Okapi([tokenize(c["text"]) for c in self.chunks])

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        filters = check_filters(filters)
        scores = self.index.get_scores(tokenize(query))
        pairs = [(s, c) for s, c in zip(scores, self.chunks)
                 if s > 0 and all(field(c, k) == v for k, v in filters.items())]
        pairs.sort(key=lambda p: (-p[0], p[1]["id"]))
        return ranked([{**c, "score": round(float(s), 4)} for s, c in pairs[:top_k]], self.method)


class HybridRetriever:
    """Phương pháp 3: Reciprocal Rank Fusion. Chỉ trộn THỨ HẠNG (không cộng thẳng 2 loại score khác thang đo)."""
    method = "hybrid_rrf"

    def __init__(self, dense: DenseRetriever, bm25: BM25Retriever, depth: int = 20, k: int = 60) -> None:
        self.dense, self.bm25, self.depth, self.k = dense, bm25, depth, k

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        fused: dict[str, dict[str, Any]] = {}
        for retriever in (self.dense, self.bm25):
            for item in retriever.search(query, filters=filters, top_k=self.depth):
                entry = fused.setdefault(item["id"], {**item, "score": 0.0, "source_ranks": {}})
                entry["score"] += 1 / (self.k + item["rank"])
                entry["source_ranks"][retriever.method] = item["rank"]
        items = sorted(fused.values(), key=lambda c: (-c["score"], c["id"]))[:top_k]
        return ranked([{**c, "score": round(c["score"], 5)} for c in items], self.method)


class RerankRetriever:
    """Cải thiện: lấy `depth` ứng viên từ retriever gốc rồi cho cross-encoder chấm lại từng cặp (câu hỏi, đoạn)."""

    def __init__(self, base: Any, depth: int = 20, model_name: str = RERANK_MODEL) -> None:
        from sentence_transformers import CrossEncoder

        self.base, self.depth = base, depth
        self.model = CrossEncoder(model_name)
        self.method = f"{base.method}+rerank"

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        candidates = self.base.search(query, filters=filters, top_k=self.depth)
        if not candidates:
            return []
        scores = self.model.predict([(query, c["text"]) for c in candidates])
        items = sorted(zip(scores, candidates), key=lambda p: (-p[0], p[1]["id"]))[:top_k]
        return ranked([{**c, "base_rank": c["rank"], "score": round(float(s), 4)} for s, c in items], self.method)