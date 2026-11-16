# Day 07 · Agentic RAG: bài nộp của Trương Thị Thu Hà (2A202603780, L3B)

Agent dùng Gemini (tool calling) truy xuất kho tài liệu Day 6 (báo cáo World Bank 2020 về giáo dục đại học Việt Nam, 82 trang, 416 chunk trong pgvector), trả lời có `[chunk-id]` hoặc từ chối khi không đủ bằng chứng. So sánh 3 phương pháp retrieval (dense, BM25, hybrid RRF) cùng 2 cấu hình cải thiện (rerank, context budget) trên dev, chốt cấu hình rồi đánh giá một lần trên test.

- Đề bài gốc: https://github.com/VinUni-AI20k/K5-L3-Day07-Retrieval-Context-Engineering (hướng dẫn gốc giữ trong `GUIDE.md`, `BENCHMARK.md`, `RUBRIC.md`…)
- **Báo cáo:** [report/individual/2A202603780_TruongThiThuHa.md](report/individual/2A202603780_TruongThiThuHa.md)
- Cấu hình đã chốt trước test: [results/LOCKED_CONFIG.md](results/LOCKED_CONFIG.md)

## Kết quả chính

| | Dev: Context Evidence Rate | Dev: grounded answer (/2) | Test: grounded answer (/2) | Abstention đúng (dev / test) |
|---|---|---|---|---|
| Baseline: dense Day 6, budget 800 | 7/15 | 1,20 (từ chối nhầm 6/15) | 1,60 | 2/2 · 2/2 |
| **Selected: hybrid RRF + rerank, budget 2400** | **14/15** | **1,87** (từ chối nhầm 1/15) | **2,00** | 2/2 · 2/2 |

**Thử thách nâng cao (+15):** index thêm 45 bảng/biểu đồ/sơ đồ do Gemini vision trích từ ảnh 82 trang. Kết quả test **30/30 (100%)** (dev 17/18), so với 20/30 nếu chỉ dùng chunk chữ. Chi tiết: mục *Thử thách nâng cao* trong báo cáo, [results/advanced/LOCKED_CONFIG.md](results/advanced/LOCKED_CONFIG.md), [results/advanced/extraction_check.md](results/advanced/extraction_check.md).

## Cấu trúc

~~~text
data/he2020/        chunks.json (xuất từ pgvector Day 6), questions.json (20 câu có gold), unanswerable.json (4 câu), cases.json (24 câu, KHÔNG có gold, agent chỉ đọc file này)
src/export_day6.py  xuất chunk + chuyển benchmark Day 6 sang schema Day 7
src/retrievers.py   Dense (pgvector) · BM25 · Hybrid RRF · Rerank (cross-encoder)
src/eval_retrieval.py  Hit@1, Evidence Hit@3, Context Evidence Rate cho mọi cấu hình
src/check_llm.py    kiểm tra key và tool calling của model
src/agent.py        controller Gemini (tool search_documents / final_answer) cho run_agent của starter
src/run_agent.py    chạy agent trên dev/test, lưu trace đầy đủ
src/make_reviews.py nhãn chấm tay (có lý do) -> reviews.json + review_sheet.md
results/retrieval/{dev,test}/   summary.md, summary.json, traces.json
results/agent/{dev,test}/{baseline,selected}/  traces.json, reviews.json, metrics.json
results/pip_freeze.txt          phiên bản thư viện
data/advanced/       questions.json (benchmark nâng cao có gold: dev 18, test 30), cases.json (không gold), visual_raw/ (kết quả vision từng trang), visual_chunks.json, chunks_all.json
src/adv_extract_visual.py · adv_index.py · adv_run.py · adv_grade.py   pipeline thử thách nâng cao
results/advanced/    index_stats.json, extraction_check.md, LOCKED_CONFIG.md, {dev,test}/{multimodal,text_only}/ traces, grades, grade_sheet.md
scripts/adv_finish.sh   chạy chấm dev -> commit chốt -> test một lần
~~~

## Cách chạy lại (macOS, Python 3.13)

Cần database Day 6 đã ingest (repo `K5-L3B-DAY06-2A202603780-DataIngestion`, Docker Desktop đang chạy).

~~~bash
# 1. Bật pgvector Day 6
docker compose -f ~/Documents/K5-L3B-DAY06-2A202603780-DataIngestion/starter/docker-compose.yml -p day6_student_starter up -d --wait

# 2. Môi trường Python
python3.13 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env      # điền LLM_API_KEY (Gemini) và LLM_MODEL=gemini-3.8-flash; KHÔNG commit .env

# 3. Dữ liệu + benchmark
python -m src.export_day6

# 4. Retrieval
python -m src.eval_retrieval --split dev
python -m src.eval_retrieval --split test --locked

# 5. Agent
python -m src.check_llm
python -m src.run_agent --split dev --config selected
python -m src.run_agent --split dev --config baseline
python -m src.run_agent --split test --config selected --locked
python -m src.run_agent --split test --config baseline --locked

# 6. Nhãn + điểm agent
python -m src.make_reviews --split dev
python -m src.make_reviews --split test
python starter/agent_metrics.py --cases data/he2020/cases.json --traces results/agent/test/selected/traces.json \
  --reviews results/agent/test/selected/reviews.json --split test --output results/agent/test/selected/metrics.json

# 7. Thử thách nâng cao (cần Docker + key Gemini)
python -m src.adv_extract_visual       # Gemini vision đọc 82 trang -> data/advanced/visual_raw/
python -m src.adv_index                # chunk bảng/hình -> pgvector strategy V
python -m src.adv_run --split dev --config multimodal
python -m src.adv_run --split test --config multimodal --locked
python -m src.adv_grade --split test --config multimodal

# Test của đề (mock, chỉ kiểm tra code)
python -m unittest discover -s tests -v
~~~

Model và dữ liệu: embedding `BAAI/bge-small-en-v1.5` (384 chiều, local), reranker `cross-encoder/ms-marco-MiniLM-L-6-v2` (local), LLM `gemini-3.8-flash` (Google Gemini API). Corpus: World Bank 2020, CC BY 3.0 IGO (http://hdl.handle.net/10986/33681).
