
#!/usr/bin/env bash
set -euo pipefail
if [[ "$EUID" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi
VENV="$(cd "$(dirname "$0")/.." && pwd)/.venv"
if [[ ! -d "$VENV" ]]; then echo "Missing venv (.venv). Run ONE_CLICK_INSTALL.sh first."; exit 1; fi
source "$VENV/bin/activate"
echo "[ML] Installing scikit-learn, lightgbm, xgboost"
pip install --upgrade pip wheel setuptools || true
pip install scikit-learn lightgbm xgboost || pip install --no-build-isolation --only-binary=:all: scikit-learn || true
python - <<'PY'
print("[ML] Versions:")
import sklearn, sys
print("sklearn:", sklearn.__version__)
try:
  import lightgbm as lgb
  print("lightgbm:", lgb.__version__)
except Exception as e: print("lightgbm: not installed", e)
try:
  import xgboost as xgb
  print("xgboost:", xgb.__version__)
except Exception as e: print("xgboost: not installed", e)
PY
