#!/usr/bin/env bash
# Thử thách nâng cao: kiểm tra bản sửa trên dev -> chấm dev -> COMMIT CHỐT CẤU HÌNH -> chạy test MỘT lần -> commit.
# Chạy từ thư mục gốc repo:  bash scripts/adv_finish.sh
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate

echo "=== 1/5 Kiểm tra bản sửa đọc JSON trên câu dev ad11 ==="
python -m src.adv_run --split dev --config multimodal --only ad11

echo "=== 2/5 Chấm dev ==="
python -m src.adv_grade --split dev --config multimodal
python -m src.adv_grade --split dev --config text_only

echo "=== 3/5 Commit chốt cấu hình TRƯỚC khi chạy test ==="
git add src/agent.py src/adv_grade.py scripts/adv_finish.sh results/advanced
git commit -m "Advanced: lock multimodal config on dev (17/18) + leaked tool-call fix, before test"
git push

echo "=== 4/5 Chạy test 30 câu (một lần) ==="
python -m src.adv_run --split test --config multimodal --locked
python -m src.adv_run --split test --config text_only --locked

echo "=== 5/5 Lưu kết quả test ==="
git add results/advanced/test
git commit -m "Advanced: single test run (multimodal locked + text_only comparison)"
git push

echo ""
echo "XONG TẤT CẢ. Nhắn Claude: xong test"
