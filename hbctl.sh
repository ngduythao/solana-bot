#!/usr/bin/env bash
set -euo pipefail
HB_ROOT="${HB_ROOT:-/opt/solanabot}"
if [ ! -d "$HB_ROOT" ]; then
  SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [ -f "$SELF_DIR/docker-compose.yml" ]; then
    HB_ROOT="$SELF_DIR"
  elif [ -f "$SELF_DIR/../docker-compose.yml" ]; then
    HB_ROOT="$(cd "$SELF_DIR/.." && pwd)"
  fi
fi
if [ ! -d "$HB_ROOT" ] || [ ! -f "$HB_ROOT/docker-compose.yml" ]; then
  echo "[ERR] Không tìm thấy thư mục dự án. Hãy giải nén vào /opt/solanabot hoặc đặt HB_ROOT=/đường/dẫn."
  exit 1
fi
cd "$HB_ROOT"
case "${1:-help}" in
  fix-docker) sudo ./fix_docker_ubuntu24.sh ;;
  check) ./check_compose.sh ;;
  diag) ./diag.sh ;;
  prod) ./scripts/prod_up.sh ;;
  bootstrap) ./bootstrap.sh ;;
  oneclick) ./oneclick.sh ;;
  run-min) make run-min ;;
  run-all) make run-all ;;
  stop) make stop || docker compose down || true ;;
  restart) make restart || (docker compose down && docker compose up -d) ;;
  logs) docker compose logs --tail=200 ;;
  *) echo "Usage: hbctl.sh {fix-docker|check|diag|prod|bootstrap|oneclick|run-min|run-all|stop|restart|logs}";;
esac
