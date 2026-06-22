
#!/usr/bin/env bash
set -euo pipefail
REDIS_CLI=${REDIS_CLI:-redis-cli}

usage() {
  cat <<EOF
hedge_ctl.sh - Live tune hedge via Redis
Usage:
  $0 set prio_mult SOL 0.8
  $0 set max_slippage_bps default 150
  $0 set allowlist BONK JUP,PHOENIX
  $0 set blacklist SOL RAYDIUM
  $0 get prio_mult SOL
  $0 get max_slippage_bps default
EOF
}

cmd=${1:-help}
case "$cmd" in
  set)
    param=${2:?param}; mint=${3:?mint}; val=${4:?val}
    key="hsbot:hedge:cfg:${param}:${mint}"
    $REDIS_CLI set "$key" "$val"
    echo "OK set $key=$val"
    ;;
  get)
    param=${2:?param}; mint=${3:?mint}
    key="hsbot:hedge:cfg:${param}:${mint}"
    echo -n "$key = "
    $REDIS_CLI get "$key"
    ;;
  *)
    usage
    ;;
esac
