#!/usr/bin/env python3
import os, time, json, datetime, glob
from urllib.parse import quote_plus
import subprocess, sys

token = os.environ.get("TELEGRAM_BOT_TOKEN","")
ids = os.environ.get("TELEGRAM_CHAT_IDS","")
if not token or not ids: sys.exit(0)

def send(msg):
    for chat in ids.split(","):
        chat = chat.strip()
        if not chat: continue
        subprocess.run(["curl","-s","-X","POST",f"https://api.telegram.org/bot{token}/sendMessage","-d",f"chat_id={chat}","-d",f"text={msg}"],stdout=subprocess.DEVNULL)

# Very simple PnL aggregation placeholder
pnl = 0.0
trades = 0
win = 0
for path in glob.glob("logs/*.csv"):
    try:
        with open(path,"r") as f:
            for line in f:
                if "pnl_usd" in line: # header skip
                    continue
                # suppose csv has pnl in last column; best-effort
                parts = [p.strip() for p in line.split(",")]
                if not parts or not parts[-1]: continue
                try:
                    val = float(parts[-1])
                    pnl += val
                    trades += 1
                    if val>0: win+=1
                except: pass
    except: pass

wr = (win/trades*100.0) if trades else 0.0
ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
msg = f"[Daily PnL] {ts}\nPnL: ${pnl:.2f}\nTrades: {trades}\nWinRate: {wr:.1f}%"
send(msg)
