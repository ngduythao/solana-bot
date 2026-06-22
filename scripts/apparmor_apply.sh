#!/usr/bin/env bash

#!/usr/bin/env bash
set -euo pipefail
if ! command -v apparmor_status >/dev/null 2>&1; then
  echo "[apparmor] not installed, skipping"; exit 0
fi
for f in security/apparmor/*.apparmor; do
  echo "[apparmor] applying $f"
  apparmor_parser -r -W "$f" || true
done
echo "[apparmor] status:"
apparmor_status || true
