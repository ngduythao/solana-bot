#!/usr/bin/env bash
redis-cli del hsbot:paused >/dev/null 2>&1 || true
#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -d ".venv" ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel >/dev/null 2>&1 || true
[ -f requirements.txt ] && pip install -r requirements.txt || true
[ -f analytics/requirements.txt ] && pip install -r analytics/requirements.txt || true
[ -x "./scripts/oneclick.sh" ] && ./scripts/oneclick.sh "${1:-auto}" || true
[ -x "./scripts/run_all.sh" ] && ./scripts/run_all.sh || true

"./scripts/serve_dashboard.sh" || true
