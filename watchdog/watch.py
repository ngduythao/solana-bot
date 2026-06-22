
# Log-only watchdog stub (no auto-restart); can be expanded to call Docker API if needed.
import os, time
SERVICES = [s.strip() for s in os.getenv("WATCH_SERVICES","redis,orchestrator,dex-dispatcher,cex-exec,hedge-exec,backrun-ws,ai-fee,priority-fee,alerting,riskcap,dashboard").split(",")]
if __name__=="__main__":
    while True:
        print("[WATCHDOG] services ok:", ",".join(SERVICES))
        time.sleep(30)
