
# Runbook — Prod incident quick guide

## Power cut / reboot loop
1) Check 24/7 panel on /pro (boot_ok, AOF). If not OK:
   - sudo systemctl status solbot_boot@$(whoami) -l --no-pager
   - sudo journalctl -u solbot_boot@$(whoami) -n 200

## RPC/Relay degrade
1) Rotate RPC in /etc/solbot/.env (fallback list) → sudo systemctl restart solbot_fast@$(whoami)
2) Reduce size: EMERGENCY_CONSERVATIVE.sh
3) Temporarily increase tip via ENV or let fee_optimizer follow tip-floor

## Tip spike / high miss-slot
1) Check /pro Jupiter Safety & Relay Tip-Curve; verify hour bucket p95
2) Tune RELAYS_CANDIDATES or micro-stagger

## Drawdown
1) Ensure guardrails active; lower COMPOUND_STEP, COMPOUND_MAX_HOT
2) If needed, EMERGENCY_CONSERVATIVE.sh (shadow mode optional)

## Key compromise suspicion
1) Rotate DASH_AUTH_TOKEN, revoke mTLS client cert
2) Move keypair file; set SIGNER_MODE=paper; clear armed flags
3) Runtime SEAL diff → audit and redeploy


## Co-lo readiness
- Mở `/pro` → xem panel *Latency Check*.
- RTT hướng NJ/SG < 1–2ms ⇒ đã đạt chuẩn co-lo. Nếu >3–5ms ổn định ⇒ cân nhắc bare-metal/co-lo.
- Script đo: `services/colo_rtt.py`; cấu hình targets: `COLO_RTT_TARGETS` trong `.env`.

## Bridge (Wormhole)
- Cài CLI: `deploy/INSTALL_WORMHOLE_CLI.sh`
- Bật HOT & arming: `SIGNER_MODE=hot`; `ARM_BRIDGE.sh 900`
- Dry-run mặc định (`BRIDGE_DRY_RUN=1`). Set `BRIDGE_DRY_RUN=0` để đánh thật.
- Nhật ký: `solbot:bridge:exec`; ngân sách: `bridge:day:<YYYY-MM-DD>:usdc`


## Circuit breaker
- Tripped khi: p95 quá cao / miss-slot lớn / drawdown sâu / vượt tip-cap.
- Tác động: xóa armed flags → dừng HOT swaps/bridge. Xem panel *Alerts & Health*.
- Reset: chờ tự hết TTL hoặc kiểm nguyên nhân, rồi arm lại `ARM_JUPITER.sh` / `ARM_BRIDGE.sh`.

## Verify
- Chạy `deploy/PREFLIGHT.sh` trước khi GO_LIVE.
- Sau go live, chạy `deploy/VERIFY_E2E.sh` (check services, metrics, keys).



## Telegram alerts
1) Cài deps: `deploy/ENABLE_TELEGRAM.sh`
2) Cấu hình `.env`:
   - TELEGRAM_BOT_TOKEN=bot<token>
   - TELEGRAM_CHAT_ID=<chat_id>
   - TELEGRAM_MIN_SEVERITY=warn (hoặc info/error/critical)
   - TELEGRAM_SILENT=0/1
3) Test: `deploy/SEND_TELEGRAM_TEST.sh`
4) Service: `solbot_telegram@<user>` tự chạy (systemd) và pull alert mới từ `solbot:alerts`.
