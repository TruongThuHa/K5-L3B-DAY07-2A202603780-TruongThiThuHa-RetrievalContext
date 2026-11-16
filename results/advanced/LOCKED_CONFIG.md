# Thử thách nâng cao · Cấu hình chốt trên dev (trước khi chạy test)

Tiêu chí (đặt trước khi xem test): (1) tỷ lệ đạt dev cao nhất theo cách chấm của ADVANCED.md; (2) không giảm ở nhóm thiếu bằng chứng; (3) hòa thì nhanh/rẻ hơn.

| Dev (18 câu) | text_only (chỉ chunk chữ Day 6) | **multimodal (chốt)** |
|---|---|---|
| Index | 416 chunk chữ (strategy B) | 416 chunk chữ + 45 chunk bảng/biểu đồ/sơ đồ do gemini-3.8-flash trích từ ảnh trang (strategy V) |
| Retrieval | hybrid RRF (dense bge-small + BM25) + rerank, depth 20, top-3, budget 2400 ký tự | như trên trên cả B+V, depth 30, top-4, budget 6000 ký tự |
| Agent | gemini-3.8-flash, tối đa 3 lần search, prompt nâng cao | tối đa 4 lần search, prompt nâng cao |
| Đạt / tổng | 10/18 (55,6%) | **17/18 (94,4%)** |
| Bảng / Sơ đồ / Biểu đồ / Multi-hop / Text / Thiếu BC | 2/4 · 2/3 · 2/4 · 0/2 · 1/2 · 3/3 | 4/4 · 3/3 · 3/4 · 2/2 · 2/2 · 3/3 |
| Trung vị thời gian | 11,0 s/câu | 6,1 s/câu |

Lỗi dev và thay đổi trước khi chốt:
- `ad11`: vision đọc đỉnh GER Hàn Quốc ≈100 (gốc ≈104) nên agent kết luận không nước nào vượt 100%. **Không sửa** nội dung trích (giữ trung thực), ghi vào giới hạn.
- `ad11` (multimodal) và `ad12` (text_only): Gemini đôi khi viết lời gọi `final_answer` thành JSON trong nội dung thay vì gọi tool, nên câu trả lời lộ JSON. **Sửa** `src/agent.py`: nhận dạng JSON này và đọc lại đúng tool/args. Chạy lại riêng `ad11` để kiểm tra (`traces_only_ad11.json`). Nội dung đúng/sai không đổi vì lỗi vision.

Quyết định: chốt `multimodal` + bản sửa đọc JSON. Test 30 câu chạy **một lần** sau commit này (multimodal, kèm text_only để so sánh).
