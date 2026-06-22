#!/usr/bin/env bash

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Candidates: profiles we already have
PROFILES=("vultr" "vultr-sg" "equinix" "balanced")

echo "[*] Auto-selecting profile based on network RTT..."
BEST=""
BESTSCORE=999999

# Helper to score RTT using tools/bench_net.sh output
score_profile() {
  local prof="$1"
  # Build a temp env by appending preset to a temp file to provide RPC/RELAYS
  local preset="configs/.env.preset.$prof"
  if [ ! -f "$preset" ]; then
    echo "skip $prof (no preset)"
    return 1
  fi
  # Extract RPC/RELAYS from preset
  local RPC=$(grep -E '^RPC_CANDIDATES=' "$preset" | head -n1 | cut -d= -f2- | tr -d '"')
  local REL=$(grep -E '^JITO_RELAYS_CANDIDATES=' "$preset" | head -n1 | cut -d= -f2- | tr -d '"')
  RPC_CANDIDATES="$RPC" JITO_RELAYS_CANDIDATES="$REL" tools/bench_net.sh > .auto_bench.out 2>/dev/null || true
  # Parse numbers (ms) and compute a simple score = avg of all lines
  local ms=$(grep -Eo '[0-9]+ms' .auto_bench.out | tr -d 'ms' | tr '\n' ' ')
  local sum=0 cnt=0
  for v in $ms; do sum=$((sum+v)); cnt=$((cnt+1)); done
  [ "$cnt" -eq 0 ] && return 1
  echo $((sum/cnt))
}

for p in "${PROFILES[@]}"; do
  sc=$(score_profile "$p" || echo 999999)
  echo " - $p score: ${sc}ms"
  if [ "$sc" -lt "$BESTSCORE" ]; then
    BESTSCORE="$sc"
    BEST="$p"
  fi
done

if [ -z "$BEST" ]; then
  echo "[!] No suitable profile found; falling back to 'balanced'"
  BEST="balanced"
fi

echo "[✓] Selected profile: $BEST (avg RTT ~${BESTSCORE}ms)"
exec ./scripts/oneclick.sh "$BEST"
