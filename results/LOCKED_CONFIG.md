# Cấu hình đã chốt trên dev (trước khi chạy test)

Tiêu chí chọn (đặt trước khi xem test), theo thứ tự ưu tiên:
1. Context Evidence Rate trên dev cao nhất (bằng chứng có thật sự tới được LLM).
2. Grounded answer trung bình trên dev cao nhất, ít từ chối nhầm nhất.
3. Abstention trên câu thiếu bằng chứng không được giảm.
4. Hòa thì chọn cấu hình nhanh/rẻ hơn.

| | baseline | selected (đã chốt) |
|---|---|---|
| Retrieval | dense Day 6 (bge-small-en-v1.5, pgvector, chunk B, filter section) | hybrid RRF (dense + BM25) + rerank cross-encoder ms-marco-MiniLM-L-6-v2 trên 20 ứng viên |
| top-k / budget | 3 / 800 ký tự | 3 / 2400 ký tự |
| Agent | gemini-3.8-flash, tối đa 3 lần search, lượt 1 = câu hỏi gốc | giống baseline |
| Dev: Context Evidence Rate | 7/15 (47%) | 14/15 (93%) |
| Dev: grounded answer trung bình | 1.20 / 2 (từ chối nhầm 6/15) | 1.87 / 2 (từ chối nhầm 1/15) |
| Dev: abstention đúng | 2/2 | 2/2 |
| Dev: thời gian trung vị / token vào+ra | 7.8 s/câu · 23 080 + 1 289 | 4.7 s/câu · 25 985 + 1 433 |

Quyết định: chọn `selected`. Test chỉ chạy một lần sau commit này, cho cả baseline và selected.