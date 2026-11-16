"""Thử thách nâng cao · Bước 1: trích bảng, biểu đồ, sơ đồ từ ảnh trang PDF bằng Gemini vision.

    python -m src.adv_extract_visual                 # mọi trang nội dung (82 trang), bỏ qua trang đã làm
    python -m src.adv_extract_visual --pages 54 56   # làm lại vài trang

- Render từng trang nội dung (cùng 82 trang đã index ở Day 6) thành PNG -> data/advanced/pages/pNNN.png (không commit,
  tạo lại được từ PDF gốc).
- Gửi ảnh trang + text pypdf của trang cho Gemini, yêu cầu trả JSON các phần tử trực quan: bảng (chép đủ ô),
  biểu đồ (trục, đơn vị, chú giải, từng giá trị), sơ đồ (từng ô chữ, cấu trúc, ý nghĩa màu).
- Lưu kết quả thô từng trang -> data/advanced/visual_raw/pNNN.json (có model, thời gian, token) để kiểm tra lại.
Nội dung do model trích KHÔNG tự đúng: các trang dùng trong benchmark được đối chiếu tay với ảnh gốc.
"""
import argparse
import base64
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pypdfium2 as pdfium
from pypdf import PdfReader

from .agent import make_client

ROOT = Path(__file__).resolve().parents[1]
PDF = Path.home() / "Documents" / "K5-L3B-DAY06-2A202603780-DataIngestion" / "starter" / "data" / "he2020.pdf"
OUT = ROOT / "data" / "advanced"
CHUNKS = ROOT / "data" / "he2020" / "chunks.json"

PROMPT = """This is page {page} of a World Bank report on higher education in Vietnam.
Extract EVERY informative visual element on the page: tables, charts/graphs, and diagrams/figures.
Ignore page headers/footers, logos, decorative images and plain running text.

Return ONLY a JSON object: {{"elements": [ ... ]}} where each element is
{{"kind": "table" | "chart" | "diagram" | "image",
  "label": "e.g. Table 7 or Figure 11 (empty string if none)",
  "title": "caption/title exactly as printed",
  "content": "see rules",
  "box_2d": [ymin, xmin, ymax, xmax]  (region of the element on the page, integers 0-1000)}}

Rules for "content":
- table: a Markdown table copying EVERY row and EVERY cell exactly as printed (numbers, n.a., dashes, units).
  Flatten multi-level headers into one header row (e.g. "2015 Target (Revised in 2013b)"). For matrix-like tables,
  keep row labels and column labels so each cell can be located. Then add the source/note lines.
- chart: chart type; x-axis and y-axis titles and units; legend entries; then EVERY data point as
  "category / series: value". Copy printed data labels exactly. If values are not printed, estimate from gridlines
  and prefix with "≈". End with 2-4 factual comparisons visible in the chart (highest, lowest, which series is above).
- diagram/image: list EVERY text box/label; describe the layout (rows, columns, levels, arrows, groupings) and what each
  colour/shading means according to the legend, stating for each cell which category it belongs to.
If the page has no informative visual element return {{"elements": []}}.

Text extracted from the page (may be garbled for tables/charts; use it only to spell words correctly):
---
{text}
---"""


def render(pdf: pdfium.PdfDocument, page: int, folder: Path) -> Path:
    path = folder / f"p{page:03d}.png"
    if not path.exists():
        pdf[page - 1].render(scale=2.0).to_pil().save(path)
    return path


def parse_json(text: str) -> dict:
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("model không trả JSON")
    data = json.loads(text[start:end + 1])
    if not isinstance(data.get("elements"), list):
        raise ValueError("JSON thiếu danh sách elements")
    return data


def extract_page(client, model: str, page: int, image: Path, page_text: str) -> dict:
    b64 = base64.b64encode(image.read_bytes()).decode()
    start = time.perf_counter()
    last_error = None
    for attempt in range(3):   # thử lại khi JSON hỏng; lỗi mạng/429 đã được SDK tự thử lại
        resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": [
            {"type": "text", "text": PROMPT.format(page=page, text=page_text[:6000])},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}])
        try:
            data = parse_json(resp.choices[0].message.content or "")
            break
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
    else:
        raise RuntimeError(f"trang {page}: {last_error}")
    return {"page": page, "model": model, "elements": data["elements"],
            "seconds": round(time.perf_counter() - start, 1), "attempts": attempt + 1,
            "tokens_in": resp.usage.prompt_tokens if resp.usage else None,
            "tokens_out": resp.usage.completion_tokens if resp.usage else None}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=PDF)
    parser.add_argument("--pages", type=int, nargs="*", help="Chỉ làm các trang này (ghi đè kết quả cũ)")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    content_pages = sorted({c["page"] for c in json.loads(CHUNKS.read_text(encoding="utf-8"))})
    pages = args.pages or content_pages
    pages_dir, raw_dir = OUT / "pages", OUT / "visual_raw"
    pages_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    todo = [p for p in pages if args.pages or not (raw_dir / f"p{p:03d}.json").exists()]
    print(f"{len(content_pages)} trang nội dung; cần trích {len(todo)} trang")

    pdf, reader = pdfium.PdfDocument(str(args.pdf)), PdfReader(str(args.pdf))
    images = {p: render(pdf, p, pages_dir) for p in todo}           # render tuần tự (pdfium không an toàn đa luồng)
    texts = {p: reader.pages[p - 1].extract_text() or "" for p in todo}
    client, model = make_client()

    def work(page: int) -> str:
        try:
            result = extract_page(client, model, page, images[page], texts[page])
        except Exception as exc:   # ghi lỗi, không bịa nội dung
            return f"p{page:03d}: LỖI {type(exc).__name__}: {exc}"
        (raw_dir / f"p{page:03d}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        kinds = ", ".join(f"{e.get('kind')}:{e.get('label') or '-'}" for e in result["elements"]) or "(không có)"
        return f"p{page:03d}: {kinds} ({result['seconds']}s)"

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for line in pool.map(work, todo):
            print(line, flush=True)
    done = len(list(raw_dir.glob("p*.json")))
    print(f"\nXong: {done}/{len(content_pages)} trang có kết quả trong data/advanced/visual_raw/")


if __name__ == "__main__":
    main()
