# Kiểm tra nội dung trích bảng/biểu đồ/sơ đồ với bản gốc

Nội dung do Gemini (gemini-3.8-flash) trích từ ảnh trang (`data/advanced/visual_raw/`) được đối chiếu **thủ công** với ảnh trang PDF gốc (render 1.4–2.0x) cho mọi bảng/hình được dùng trong benchmark dev/test. Kiểm tra trước khi chạy agent.

Tổng quan: 82/82 trang nội dung được gửi cho vision model; tìm thấy 45 phần tử (28 bảng, 14 biểu đồ, 3 sơ đồ), khớp đủ 22 bảng + 17 hình của mục lục (thêm các bảng ES.1/ES.2 dài nhiều trang ở tr. 24–29). Không có trang lỗi.

| Trang | Phần tử | Kết quả đối chiếu |
|---|---|---|
| 20 | Figure ES.3 (biểu đồ cột có nhãn) | Đúng cả 13 giá trị (0,33 … 1,89) |
| 34 | Figure 2 (sơ đồ khung phân tích) | Đúng đủ 4 tầng, mọi ô chữ |
| 37 | Figure 3 (biểu đồ đường, không nhãn) | **Sai lệch:** đỉnh Hàn Quốc ghi ≈100% (2008–2009), ảnh gốc ≈104% (vượt vạch 100 khoảng 2007–2011). Các đường khác hợp lý |
| 38 | Table 1 | Đúng mọi ô |
| 40 | Table 2, Figure 6 (có nhãn) | Đúng mọi ô / mọi nhãn |
| 41 | Figure 7 (cột chồng, không nhãn) | Ước lượng hợp lý; Female–Male ≈13 nhỏ nhất, Q5–Q1 ≈67 lớn nhất |
| 43 | Table 3 | Đúng mọi ô |
| 44 | Table 4 | Đúng mọi ô |
| 45 | Figure 8, Figure 9 (không nhãn) | Ước lượng hợp lý; thứ tự cột đúng (25–35 > ALL ở Primary, Secondary; "Does not apply" cao nhất ở Foreign language ≈0,25) |
| 50 | Table 5 | Đúng mọi ô (18 nước × 6 cột) |
| 51 | Figure 10 (có nhãn) | Đúng 19 giá trị; lỗi chính tả nhỏ "Switzeland" (giữ nguyên, không ảnh hưởng) |
| 52, 58, 60, 62, 68, 79 | Table 6, 9, 11, 13, 14, 17; Figure 12 | Đúng mọi ô / nhãn |
| 54 | Table 7 | Đúng (Student/lecturer ratio: thực tế 2015 = 23; mục tiêu 2020 = 20 và 17–26) |
| 56 | Figure 11 (sơ đồ lưới có màu) | Đúng màu cả 20 ô theo chú giải (cam = Don't exist, xám = Partially exist) |
| 61 | Table 12 (bảng ma trận) | Đúng ô (>40 × <0,5) = Vietnam, Mongolia |
| 67 | Figure 13 (đường, không nhãn) | Ước lượng hợp lý (primary ≈36% → ≈24%) |
| 80 | Figure 14 (sơ đồ) | Đúng mọi ô; giữ lỗi chính tả của bản gốc ("Buiding", "adotion") |

Ảnh hưởng đã biết: câu dev `ad11` (Hàn Quốc vượt 100% GER) dựa vào Figure 3, nơi model đọc thấp hơn gốc. Không sửa tay nội dung trích để kết quả benchmark phản ánh đúng pipeline.
