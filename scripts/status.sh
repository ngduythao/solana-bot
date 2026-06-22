#!/usr/bin/env bash
set -euo pipefail
echo '== tmux sessions =='
tmux ls 2>/dev/null || echo '(no tmux sessions)'
echo
echo 'Tip mult:'; redis-cli get hsbot:tip:mult_effective 2>/dev/null || true
echo 'Notional mult:'; redis-cli get hsbot:notional:mult_effective 2>/dev/null || true
