#!/usr/bin/env bash

#!/usr/bin/env bash
set -euo pipefail
echo "== tail metrics.csv =="
tail -n 50 metrics.csv 2>/dev/null || echo "(metrics.csv not found yet)"
