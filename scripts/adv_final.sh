#!/usr/bin/env bash
# Chấm test thử thách nâng cao + lưu báo cáo cuối.  Chạy: bash scripts/adv_final.sh
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
echo "=== Chấm test ==="
python -m src.adv_grade --split test --config multimodal
python -m src.adv_grade --split test --config text_only
echo "=== Commit + push ==="
git add src/adv_grade.py scripts/adv_final.sh results/advanced README.md report/individual/2A202603780_TruongThiThuHa.md
git commit -m "Advanced: test labels and grades (multimodal 30/30, text_only 20/30), final report and README"
git push
echo ""
echo "XONG. Nhắn Claude: xong"
