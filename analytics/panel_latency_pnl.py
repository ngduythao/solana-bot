
import os, sys, pandas as pd
from datetime import datetime, timedelta

METRICS_PATH = os.getenv("METRICS_PATH", "metrics.csv")

def main():
    if not os.path.exists(METRICS_PATH):
        print("No metrics yet:", METRICS_PATH); return
    df = pd.read_csv(METRICS_PATH)
    if df.empty:
        print("Empty metrics"); return
    # Simple views
    recent = df.tail(2000)
    print("=== Recent kinds count ===")
    print(recent["kind"].value_counts())
    if "latency_ms" in recent.columns:
        print("\nLatency ms (describe):")
        print(recent["latency_ms"].describe())
    if {"route","pnl_usd","latency_ms"}.issubset(set(recent.columns)):
        recent["pnl_per_s"] = recent["pnl_usd"] / (recent["latency_ms"].clip(lower=1)/1000.0)
        top = recent.sort_values("pnl_per_s", ascending=False).head(20)
        print("\nTop routes by PnL/s (recent):")
        print(top[["ts","route","pnl_usd","latency_ms","pnl_per_s","note"]])
if __name__ == "__main__":
    main()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)

def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
