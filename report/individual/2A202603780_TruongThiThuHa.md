# Báo cáo Day 7 · Agentic RAG — Trương Thị Thu Hà (2A202603780, L3B)

Repo: `K5-L3B-DAY07-2A202603780-TruongThiThuHa-RetrievalContext` · Tiếp nối Day 6: `K5-L3B-DAY06-2A202603780-DataIngestion`

## Dữ liệu và benchmark

- **Nguồn, quyền sử dụng, số trang và số chunk:** World Bank (2020), *Improving the Performance of Higher Education in Vietnam: Strategic Priorities and Policy Options* (http://hdl.handle.net/10986/33681), giấy phép **CC BY 3.0 IGO** (được dùng và chia sẻ lại, có ghi nguồn). PDF 102 trang, index **82 trang nội dung** (bỏ bìa, mục lục, trang trắng, tài liệu tham khảo, như manifest Day 6). Dùng lại **416 chunk** của cấu hình B Day 6 (cắt theo đoạn/câu, tối đa 800 ký tự), mỗi chunk có `section` (executive_summary 85, introduction 25, diagnosis 129, policy_options 177).
- **Vector store, embedding model, phiên bản và số chiều:** PostgreSQL 16 + **pgvector 0.8.7** (Docker từ repo Day 6, cổng 55433), khoảng cách cosine, exact search. Embedding **BAAI/bge-small-en-v1.5** (sentence-transformers 6.3.0, chạy local), **384 chiều**, vector chuẩn hóa; câu hỏi thêm tiền tố BGE như Day 6. Day 7 **không tạo lại embedding**: `DenseRetriever` truy vấn thẳng bảng `chunks` (strategy B) và kiểm tra `vector_dims = 384` cùng tên `embedding_model` khớp trước khi chạy. Chunk được xuất ra `data/he2020/chunks.json` (`src/export_day6.py`, chỉ gộp khoảng trắng, nội dung giữ nguyên) để chạy BM25/TF-IDF và chấm.
- **Agent model, cách chạy và phân chia dev/test:** **gemini-3.8-flash** qua cổng tương thích OpenAI của Google (thư viện `openai`, tool calling). Chạy: `python -m src.run_agent --split dev|test --config baseline|selected`. Benchmark **24 câu**: dev 15 có đáp án + 2 thiếu bằng chứng; test 5 + 2. 20 câu có đáp án lấy từ benchmark Day 6 (đã chia theo trang nguồn trước thử nghiệm ở Day 6; test Day 6 chỉ chạy một lần, chưa dùng để chỉnh). Thêm 4 câu thiếu bằng chứng mới (n01–n04). Toàn bộ benchmark được commit (`4644096`) **trước mọi thử nghiệm Day 7**.
- **Cách xác định câu có/thiếu evidence và tiêu chí chấm:** câu có đáp án ghi nguồn, trang và evidence nguyên văn. Mỗi evidence phải nằm trọn trong một chunk đúng nguồn và trang (code kiểm tra 20/20; `q14` và trang 26 của `q18` chỉ khớp sau khi gộp khoảng trắng). Câu thiếu bằng chứng được chọn gần chủ đề (tỷ lệ bỏ học, tỷ lệ SV/giảng viên, số tuần đóng cửa vì COVID-19, lương giảng viên). Đã kiểm tra bằng tìm từ khóa trong 416 chunk và Cmd+F trên PDF; lý do ghi trong `data/he2020/unanswerable.json`. Chấm theo `BENCHMARK.md`: hit = chunk đúng nguồn + trang và chứa nguyên văn evidence; câu thiếu bằng chứng không tính vào mẫu số retrieval. Agent chỉ đọc `data/he2020/cases.json` (id, câu hỏi, filter), **không có gold**.

## Retrieval và thử nghiệm

Ba phương pháp (`src/retrievers.py`), cùng corpus, index, câu hỏi và định nghĩa hit (`hit`, `pack_context` của starter):
1. **Dense (baseline):** bge-small-en-v1.5 → pgvector cosine, tương đương cấu hình C của Day 6.
2. **BM25** (`rank-bm25`, tách từ `\w+` chữ thường) trên `chunks.json`.
3. **Hybrid RRF:** lấy top-20 của dense và top-20 của BM25, hợp nhất bằng Reciprocal Rank Fusion (k = 60). Chỉ trộn **thứ hạng**, không cộng hai loại score khác thang đo.
- **Cải thiện 1:** hybrid + **rerank** 20 ứng viên bằng cross-encoder `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- **Cải thiện 2:** giữ cải thiện 1, tăng **context budget từ 800 lên 2400 ký tự**.
- **Filter:** `section` lấy từ trường `filter` do người dùng cung cấp trước trong câu hỏi (q12, q13, q18), áp dụng cho dense, BM25 và hybrid. TF-IDF của starter không có filter. Không suy filter từ gold.

Lệnh: `python -m src.eval_retrieval --split dev` / `--split test --locked`. Kết quả: `results/retrieval/{dev,test}/summary.md`, trace từng câu trong `traces.json`. Thời gian là trung vị ms/câu trên MacBook Air (CPU). Chi phí retrieval **0 USD** (chạy local).

| Cấu hình | Phương pháp, top-k, filter, rerank, context budget | Giả thuyết / thay đổi | Split | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Thời gian / chi phí |
|---|---|---|---|---|---|---|---|
| (tham khảo) TF-IDF starter | lexical TF-IDF, k=3, không filter, 800 ký tự | baseline offline của đề | dev | 7/15 (47%) | 12/15 (80%) | 5/15 (33%) | 1,0 ms · 0 USD |
| Baseline | dense Day 6, k=3, filter section, không rerank, 800 ký tự | cấu hình C của Day 6 | dev | 9/15 (60%) | 12/15 (80%) | 7/15 (47%) | 43 ms · 0 USD |
| Phương pháp 2 | BM25, k=3, filter section, 800 ký tự | bắt được số liệu và tên riêng mà dense bỏ sót | dev | 7/15 (47%) | 13/15 (87%) | 8/15 (53%) | 1,2 ms · 0 USD |
| Phương pháp 3 | hybrid RRF (dense + BM25, depth 20), k=3, filter, 800 ký tự | hai cách bù lỗi cho nhau | dev | 10/15 (67%) | 14/15 (93%) | 8/15 (53%) | 38 ms · 0 USD |
| Cải thiện 1 | hybrid + rerank cross-encoder (20 ứng viên), k=3, 800 ký tự | xếp lại để đoạn đúng lên hạng 1 | dev | 13/15 (87%) | 14/15 (93%) | 8/15 (53%) | 131 ms · 0 USD |
| Cải thiện 2 | như cải thiện 1, **budget 2400 ký tự** | budget 800 chỉ vừa khoảng 1 chunk nên bỏ mất đoạn đúng | dev | 13/15 (87%) | 14/15 (93%) | **14/15 (93%)** | 227 ms · 0 USD |
| Cấu hình đã chọn | = cải thiện 2 | chạy một lần sau khi chốt | test | 5/5 (100%) | 5/5 (100%) | **5/5 (100%)** | 102 ms · 0 USD |
| Baseline | dense, 800 ký tự | chạy một lần sau khi chốt | test | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 38 ms · 0 USD |

Phương pháp 3 (hybrid) vừa là phương pháp mới vừa là cải thiện so với baseline. Cải thiện 1 và 2 được đo riêng để thấy tác động của từng thay đổi.

**Lỗi dev 1 · Context budget làm rơi đoạn đúng.** Với cải thiện 1, Hit@1 đạt 13/15 nhưng Context Evidence Rate chỉ 8/15. Đọc trace (`q03`, `q04`) thấy chunk dài tới 800 ký tự, cộng dòng nguồn thì vượt budget 800, nên `pack_context` **bỏ chunk hạng 1** và nhét chunk ngắn hơn ở hạng sau (sai). *Giả thuyết:* tăng budget lên khoảng 3 chunk sẽ giữ được evidence. *Kết quả:* budget 2400 cho context 8/15 → **14/15**; ở mức agent, câu trả lời đúng tăng 9/15 → 14/15 (xem dưới). *Đánh đổi:* prompt dài hơn khoảng 1.600 ký tự mỗi lượt.

**Lỗi dev 2 · Evidence nằm trong bảng (`q14`, trang 75).** Mọi phương pháp đều trượt. Bảng "Types of Contracts for Permanent Academic Staff" bị pypdf trích thành chữ rời theo cột. Evidence nằm ở chunk `p075-B01`, còn retrieval chỉ lấy được `p075-B00` (cùng trang, khác đoạn). Agent đã thử viết lại câu tìm 3 lần ("Table 16 Types of Contracts…", "\"Fixed-term contracts\" \"Drawbacks\"") nhưng vẫn chỉ ra `p075-B00`. *Chưa sửa*; cách khả thi là trích bảng thành dòng có tiêu đề cột khi ingest. Đây là giới hạn của bài.

**Lỗi dev 3 (mức agent) · `q01` bị từ chối oan.** Lần chạy đầu, agent tìm 3 lần bằng câu tự viết lại. Context **đã có** đoạn trang 40 ("54 in 2016"), nhưng câu hỏi nói "current" nên model tiếp tục tìm. Hết lượt, model trả lời bằng chữ thường với citation gộp `[id1, id2]`, code không đọc được nên chuyển thành abstain (3 lần search, 25 giây). *Sửa:* lượt 1 luôn tìm bằng **câu hỏi gốc** (giống benchmark retrieval), prompt dặn "context đủ thì trả lời ngay, ghi kèm năm", chuẩn hóa mọi kiểu ghi citation. *Sau khi sửa:* `q01` được trả lời đúng `[he2020-p015-B00]`, 1 lần search, 6,8 giây.

**Tiêu chí chọn và chốt cấu hình** (`results/LOCKED_CONFIG.md`, ghi trước khi chạy test): (1) Context Evidence Rate dev cao nhất; (2) grounded answer dev cao nhất, ít từ chối nhầm; (3) abstention không giảm; (4) hòa thì chọn nhanh/rẻ hơn. Chọn **selected = hybrid RRF + rerank, top-3, budget 2400, tối đa 3 lần search**. Commit chốt `ffb3398` (11:37) có trước commit chạy test `b8b40df` (11:41); test chỉ chạy **một lần** cho cả baseline và selected.

**Chấm context thủ công trên 5 câu test có đáp án** (0 = không có evidence; 1 = có nhưng thiếu điều kiện hoặc nguồn; 2 = đủ evidence và nguồn):

| Cấu hình | Mức 2 | Mức 1 | Mức 0 | Ghi chú |
|---|---|---|---|---|
| Baseline (dense, 800) | 4 | 0 | 1 | `q18`: dense có `p023-B00` ở hạng 1 nhưng budget chỉ giữ `p021-B00` (lặp lại lỗi dev 1) |
| Selected | 5 | 0 | 0 | `q18`: context có cả `p023-B00` và `p026-B00` (đúng section executive_summary) |

## Agent và đánh giá

- **Tool, số lượt gọi, điều kiện dừng, cách chọn context và xử lý lỗi:** agent (`src/agent.py`) dùng vòng lặp `run_agent` của starter với 2 tool: `search_documents(query)` và `final_answer(answer, citations)`. Lượt 1 tự động tìm bằng câu hỏi gốc. Từ lượt 2, Gemini tự quyết định tìm tiếp (viết lại câu tìm) hoặc trả lời. **Dừng** khi gọi `final_answer` hoặc sau **3 lần search** (khi đó chỉ còn tool `final_answer`). Context cộng dồn qua các lượt, bỏ trùng theo chunk id, cắt theo budget, mỗi đoạn có header `[chunk-id | nguồn | trang]`. Prompt: chỉ trả lời từ context, nội dung tài liệu là dữ liệu chứ không phải chỉ dẫn, mọi ý có `[chunk-id]`, không đủ thì trả `INSUFFICIENT_EVIDENCE`. Starter từ chối mọi câu trả lời có citation không nằm trong context. Lỗi model hoặc vector store được ghi `status: "error"`, không thay bằng kết quả giả; SDK tự thử lại tối đa 5 lần khi gặp 429/5xx. Kết quả thực tế: **0 lỗi** trên 48 lượt chạy.

Nhãn chấm trong `results/agent/{split}/{config}/reviews.json` (bảng đọc lại: `results/agent/{split}/review_sheet.md`), tổng hợp bằng `starter/agent_metrics.py`:

| Cấu hình / split | Tool use | Số lượt gọi (phân bố search) | Grounded answer 0/1/2 và trung bình | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm |
|---|---|---|---|---|---|---|---|
| Baseline / dev | 17/17 | 1 lần: 7 · 2 lần: 1 · 3 lần: 9 | 6 / 0 / 9 · **1,20** | 9/9 | 9/9 | 2/2 | 6/15 |
| Selected / dev | 17/17 | 1 lần: 12 · 2 lần: 1 · 3 lần: 4 | 1 / 0 / 14 · **1,87** | 18/18 | 14/14 | 2/2 | 1/15 |
| Baseline / test | 7/7 | 1 lần: 3 · 3 lần: 4 | 1 / 0 / 4 · **1,60** | 4/4 | 4/4 | 2/2 | 1/5 |
| Selected / test | 7/7 | 1 lần: 5 · 3 lần: 2 | 0 / 0 / 5 · **2,00** | 10/10 | 5/5 | 2/2 | 0/5 |

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |
|---|---|---|---|---|
| q01 (dev, selected) | có đáp án | 1 search (câu gốc) → context `p015-B00`, `p040-B02` (cả hai chứa evidence) | "About 54 percent of Vietnam's current 2.3 million higher education students are female." `[he2020-p015-B00]` | grade 2; citation ✅ (trang 15 nêu nguyên văn) |
| q18 (test, selected) | có đáp án, filter `executive_summary` | 1 search, filter `section=executive_summary` → context `p023-B00`, `p021-B00`, `p026-B00` | "…raise the share of public funding … from the current 0.23 percent to at least 0.8 percent of GDP by 2030." `[p023-B00] [p026-B00]` | grade 2; 2/2 citation ✅; baseline cùng câu bị từ chối nhầm (budget) |
| n04 (test, selected) | thiếu bằng chứng | 3 search (câu gốc, "lecturer salary faculty remuneration wage", "… monthly VND …") → chỉ thấy trang 44–45 về thu nhập người tốt nghiệp | "Không đủ bằng chứng để trả lời." | abstention đúng; không lấy nhầm thu nhập người tốt nghiệp (trang 44) |
| q14 (dev, selected) | có đáp án (bảng) | 3 search, chỉ tìm được `p075-B00` | từ chối | grade 0 — lỗi retrieval với bảng (lỗi dev 2) |

- **Đường dẫn trace, nhãn, lệnh chạy, thời gian và chi phí:** trace agent `results/agent/{dev,test}/{baseline,selected}/traces.json` (từng tool call, query, kết quả, context, câu trả lời, citation, token, thời gian, lỗi); nhãn `reviews.json`; điểm `metrics.json`; chốt cấu hình `results/LOCKED_CONFIG.md`. Thời gian trung vị: selected **4,7 s/câu (dev), 5,1 s/câu (test)**; baseline 7,8 s và 8,4 s, chậm hơn vì từ chối nhầm nên tìm đủ 3 lần. Token LLM (vào + ra): dev selected 25.985 + 1.433, dev baseline 23.080 + 1.289, test selected 10.795 + 714, test baseline 9.077 + 523. Tổng khoảng 69 nghìn token vào và 4 nghìn token ra; chi phí tính theo bảng giá Gemini API tại thời điểm chạy (báo số token để quy đổi).
- **Kết quả trước/sau, ví dụ lỗi, đánh đổi và giới hạn:**
  - *Trước/sau:* baseline → selected trên dev: grounded 1,20 → 1,87, từ chối nhầm 6/15 → 1/15, thời gian 7,8 → 4,7 s/câu; trên test: 1,60 → 2,00. Abstention giữ 2/2 ở cả hai split.
  - *Đánh đổi:* rerank thêm khoảng 60–190 ms/câu retrieval (CPU) và một model 90 MB; budget 2400 tăng token vào khoảng 13% (dev). Bù lại agent ít phải tìm lại nên tổng thời gian giảm.
  - *Giới hạn:* (1) bảng/biểu đồ bị trích thành chữ rời (`q14`); (2) test nhỏ (5 + 2 câu) nên kết quả 100% dao động lớn, không kết luận mạnh; (3) chấm hit bằng khớp nguyên văn evidence trong một chunk, câu có nhiều đoạn hợp lệ dựa vào danh sách evidence thay thế; (4) LLM không cố định seed nên chạy lại có thể khác nhẹ; (5) nhãn chấm được Claude (AI) soạn sau khi đọc từng câu trả lời và từng đoạn trích; học viên đã đọc lại và xác nhận toàn bộ nhãn dev, đối chiếu đoạn trích trong `chunks.json`. Benchmark Day 6 cũng được soạn có AI hỗ trợ và đã đối chiếu với PDF. (6) **Lỗi benchmark phát hiện sau khi chạy test** (khi làm thử thách nâng cao): câu dev `n02` ("student-to-lecturer ratio in Vietnamese public universities") được coi là thiếu bằng chứng do mình chỉ tìm cụm "student-lecturer". Thực tế Table 7 (trang 54) có "Student/lecturer ratio" toàn hệ thống, năm 2015 là 23. Câu hỏi nói riêng *public universities* nên nhãn "từ chối đúng" là trường hợp ranh giới; nếu coi `n02` là câu có đáp án thì từ chối nhầm dev của selected là 2/16 thay vì 1/15. Không đổi nhãn sau khi xem kết quả; bài học là kiểm tra câu thiếu bằng chứng cả trong bảng (đã áp dụng cho benchmark nâng cao). (7) Sau khi chạy test phần cơ bản, `src/agent.py` có thêm 2 thay đổi cho thử thách nâng cao: prompt hệ thống có thể truyền vào, và nhận dạng lời gọi tool bị Gemini viết thành JSON trong nội dung. Thay đổi thứ hai chỉ có tác dụng khi lỗi đó xảy ra; trace phần cơ bản không có trường hợp này nên không chạy lại.
  - *Sử dụng AI:* code trong `src/` được viết với hỗ trợ của Claude theo `AGENT_SETUP.md`; học viên chạy toàn bộ lệnh trên máy mình, đọc trace và chịu trách nhiệm kết quả.

## Thử thách nâng cao (nếu thực hiện)

**Kết quả: test 30/30 (100%) với cấu hình chốt `multimodal`, vượt ngưỡng 27/30; không có lỗi hệ thống.**

- **Tài liệu, nguồn, quyền sử dụng, số trang và phiên bản:** cùng tài liệu phần cơ bản: World Bank (2020), *Improving the Performance of Higher Education in Vietnam*, CC BY 3.0 IGO, http://hdl.handle.net/10986/33681. PDF **102 trang** (SHA-256 `5d11b0bb…948cd`, file `starter/data/he2020.pdf` trong repo Day 6), có **22 bảng, 17 hình** (14 biểu đồ, 3 sơ đồ) và các bảng ES.1–ES.2 dài nhiều trang. Index **82 trang nội dung**; 20 trang không index là bìa, bản quyền, mục lục, danh mục viết tắt, lời cảm ơn (tr. 1–12), 2 trang trắng (30, 36) và tài liệu tham khảo/bìa sau (97–102). Các trang này không chứa thông tin dùng để trả lời.
- **Cách xử lý text, bảng, ảnh, biểu đồ; phạm vi index và phần chưa xử lý:**
  - *Text:* giữ 416 chunk chữ của Day 6 (strategy `B`).
  - *Bảng/biểu đồ/sơ đồ* (`src/adv_extract_visual.py`): render **cả 82 trang** thành ảnh (pypdfium2, scale 2), gửi ảnh và text pypdf của trang cho **gemini-3.8-flash (vision)**, yêu cầu trả JSON từng phần tử. Bảng được chép thành Markdown đủ ô (header nhiều tầng làm phẳng). Biểu đồ ghi trục, đơn vị, chú giải và từng giá trị (nhãn in sẵn thì chép, không có thì ước lượng và đánh dấu ≈). Sơ đồ ghi mọi ô chữ, cấu trúc và **ý nghĩa màu theo chú giải**. Kết quả: **45 phần tử** (28 bảng, 14 biểu đồ, 3 sơ đồ) trên 41 trang, đủ 22 bảng + 17 hình; 0 trang lỗi; 182.802 token vào + 24.700 token ra, khoảng 12,6 phút tổng thời gian gọi model.
  - *Index* (`src/adv_index.py`): mỗi phần tử thành 1 chunk `he2020-pNNN-VKK`, dòng đầu `[Table 5: tiêu đề] (page 50, table)`. Metadata giữ trang, loại, nhãn, tiêu đề, **vùng trang `box_2d`** (0–1000) và đường dẫn ảnh trang để kiểm chứng. Embed bằng đúng bge-small-en-v1.5 (384 chiều), lưu vào pgvector với strategy `V`. Retrieval nâng cao tìm trên cả `B,V` (461 chunk).
  - *Kiểm chứng:* nội dung trích của **mọi bảng/hình dùng trong benchmark** được đối chiếu tay với ảnh trang gốc **trước khi chạy agent** (`results/advanced/extraction_check.md`). Bảng và biểu đồ có nhãn số đều đúng từng ô; màu 20 ô của Figure 11 đúng. **Một sai lệch:** Figure 3 (biểu đồ đường không nhãn) model đọc đỉnh GER Hàn Quốc ≈100%, gốc ≈104%. Không sửa tay để kết quả phản ánh đúng pipeline.
  - *Chưa xử lý:* không crop ảnh riêng từng hình (dùng ảnh trang + `box_2d`); giá trị biểu đồ không có nhãn là ước lượng.
- **Cách chia benchmark, schema evidence, model và cấu hình đã chốt trên dev:** `data/advanced/questions.json` (gold) và `cases.json` (agent chỉ đọc file này, không có đáp án). **Dev 18 câu** (bảng 4, sơ đồ 3, biểu đồ 4, multi-hop 2, text 2, thiếu bằng chứng 3) và **test 30 câu** (bảng 6, sơ đồ 5, biểu đồ 5, multi-hop 4, text 4, thiếu bằng chứng 6), không trùng câu trả lời, **commit `3929452` trước mọi thử nghiệm**. Mỗi câu có nhóm chính, đáp án, **tiêu chí chấm** (đơn vị, phần bắt buộc), evidence theo trang + tên bảng/hình + **vùng** (hàng × cột, cột/đường trong biểu đồ, ô trong sơ đồ). Câu thiếu bằng chứng ghi cách kiểm tra. Đáp án soạn bằng cách đọc ảnh trang gốc; câu thiếu bằng chứng được kiểm tra trong text **và** trong bảng (sau bài học `n02`). So sánh trên dev (`results/advanced/LOCKED_CONFIG.md`): `text_only` (cấu hình chốt phần cơ bản) **10/18** so với `multimodal` (B+V, hybrid RRF + rerank depth 30, top-4, budget 6000 ký tự, tối đa 4 lần search, prompt nâng cao: tìm theo nhãn bảng/hình, đọc ô theo cả hàng và cột, dùng chú giải màu, cho phép phép tính đơn giản) **17/18**. Lỗi dev: `ad11` (lỗi vision Figure 3, không sửa) và lỗi Gemini **viết lời gọi tool thành JSON trong nội dung** (`ad11`, `ad12`). Đã sửa `src/agent.py` để đọc lại JSON đó và kiểm tra lại riêng `ad11`. Commit chốt `abf2865` (12:37) có trước commit chạy test `8e90253` (12:47); test chạy **một lần**.

| Nhóm test | Đạt / tổng | Tỷ lệ | Lỗi / nhận xét |
|---|---|---|---|
| Bảng | 6/6 | 100% | Đọc đúng ô theo hàng × cột, kể cả bảng ma trận (Table 12). text_only: 5/6 |
| Ảnh, sơ đồ | 5/5 | 100% | Đúng cả câu cần đọc **màu** ô (Figure 11). text_only: 2/5 (text không có màu) |
| Biểu đồ | 5/5 | 100% | Đúng cả biểu đồ không nhãn số (Figure 8, 9, 13). text_only: 2/5 |
| Multi-hop | 4/4 | 100% | Ghép 2 bảng/hình ở 2 trang, có phép so sánh/trừ. text_only: 2/4 |
| Text | 4/4 | 100% | text_only: 4/4 |
| Thiếu bằng chứng | 6/6 | 100% | Không lấy số khác năm/khác nhóm. text_only: 5/6 (`at25` lấy GERD 2015 trả lời cho 2020) |
| **Toàn bộ** | **30/30** | **100%** | 0 lỗi hệ thống; text_only 20/30 (66,7%) |

- **Trace, nhãn và evidence từng câu; thời gian, chi phí, lỗi hệ thống:** trace `results/advanced/test/multimodal/traces.json` (tool call, query, kết quả, context, câu trả lời, citation, token, thời gian); nhãn đạt/không đạt kèm lý do và evidence trang/vùng trong `src/adv_grade.py` → `results/advanced/test/multimodal/grades.json` và `grade_sheet.md` (mỗi câu: câu hỏi, đáp án chuẩn, tiêu chí, evidence gốc, câu trả lời, đoạn được trích). Mọi câu có đáp án đều trích chunk trên **đúng trang gold** (kiểm tra tự động + đọc tay). Thời gian trung vị **5,95 s/câu**; số lần search: 1 lần 21 câu, 2 lần 3 câu, 4 lần 6 câu (cả 6 câu thiếu bằng chứng tìm đủ 4 lần rồi mới từ chối). Token agent test: 96.892 vào + 2.676 ra. Lỗi hệ thống: 0. Retrieval và embedding chạy local (0 USD); chi phí API Gemini gồm bước vision (khoảng 207 nghìn token) và agent dev/test.
- **Giới hạn, cách tái lập và đường dẫn benchmark:** (1) test 30 câu vẫn nhỏ; 100% không có nghĩa hệ thống không sai: dev có 1 lỗi do vision đọc sai biểu đồ đường không nhãn; (2) giá trị biểu đồ không nhãn là ước lượng ±1–2 điểm, câu hỏi dạng này được thiết kế hỏi so sánh/xu hướng thay vì số chính xác; (3) câu hỏi và nhãn do Claude (AI) soạn sau khi đọc ảnh trang gốc và từng câu trả lời; học viên chịu trách nhiệm và đã kiểm tra lại; (4) cùng một tài liệu được dùng cho benchmark và phát triển (đề cho phép), nhưng cấu hình chỉ chọn trên dev. Tái lập: `python -m src.adv_extract_visual` → `python -m src.adv_index` → `python -m src.adv_run --split test --config multimodal --locked` → `python -m src.adv_grade --split test --config multimodal` (chi tiết trong `README.md`). Benchmark: `data/advanced/questions.json`; trích xuất thô: `data/advanced/visual_raw/`; chunk: `data/advanced/visual_chunks.json`; thống kê index: `results/advanced/index_stats.json`.
