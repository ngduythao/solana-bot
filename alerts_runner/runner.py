
import os, time, json, redis, pandas as pd, numpy as np
import httpx, asyncio

REDIS_URL = os.getenv("REDIS_URL","redis://redis:6379/0")
CSV_PATH = os.getenv("CSV_PATH","/app/analytics.csv")
WEBHOOK = os.getenv("ALERT_WEBHOOK","")
TG_TOK = os.getenv("ALERT_TG_TOKEN","")
TG_CHAT = os.getenv("ALERT_TG_CHAT","")

DRIFT_WARN = float(os.getenv("DRIFT_WARN","5"))
DRIFT_SPIKE_COUNT = int(os.getenv("DRIFT_SPIKE_COUNT","5"))
DRIFT_WINDOW_MIN = int(os.getenv("DRIFT_WINDOW_MIN","10"))
MISS_SLOT_AGE_S = int(os.getenv("MISS_SLOT_AGE_S","5"))
MISS_SLOT_COUNT = int(os.getenv("MISS_SLOT_COUNT","3"))
HOURLY_DD_BPS = float(os.getenv("HOURLY_DD_BPS","60"))
NAV_USD = float(os.getenv("NAV_USD","10000"))
PAUSE_MINUTES = int(os.getenv("PAUSE_MINUTES","15"))
AUTO_SIZE_FACTOR_MIN=float(os.getenv('AUTO_SIZE_FACTOR_MIN','0.5'))

r = redis.from_url(REDIS_URL)

async def send_webhook(level, msg):
    if not WEBHOOK: return
    try:
        async with httpx.AsyncClient(timeout=2.0) as c:
            await c.post(WEBHOOK, json={"level":level, "message":msg})
    except Exception:
        pass

async def send_tg(text):
    if not TG_TOK or not TG_CHAT: return
    url = f"https://api.telegram.org/bot{TG_TOK}/sendMessage"
    data = {"chat_id": TG_CHAT, "text": text[:4000], "disable_web_page_preview": True}
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            await c.post(url, json=data)
    except Exception:
        pass

def pause_pair(pair: str, minutes: int):
    until = int(time.time()) + minutes*60
    r.set(f"paused:{pair}", str(until))

def check_drift_spike():
    if not os.path.exists(CSV_PATH): return []
    try:
        df = pd.read_csv(CSV_PATH)
        if 'ts' not in df.columns or 'drift_bps' not in df.columns or 'pair' not in df.columns:
            return []
        df['ts'] = pd.to_datetime(df['ts'])
        tcut = pd.Timestamp.utcnow() - pd.Timedelta(minutes=DRIFT_WINDOW_MIN)
        recent = df[df['ts']>=tcut]
        out=[]; 
        for pair, sub in recent.groupby('pair'):
            cnt = int((sub['drift_bps'].abs() > DRIFT_WARN).sum())
            if cnt >= DRIFT_SPIKE_COUNT: out.append((pair,cnt))
        return out
    except Exception:
        return []

def check_miss_slots():
    try:
        ts = int((r.get("slot:ts") or b"0").decode())
        age = int(time.time()) - ts if ts>0 else 999
        miss = int((r.get("miss:count") or b"0").decode())
        if age > MISS_SLOT_AGE_S: miss += 1
        else: miss = max(0, miss-1)
        r.set("miss:count", str(miss))
        return age, miss
    except Exception:
        return 999, 0

def hourly_dd_bps():
    if not os.path.exists(CSV_PATH): return 0.0
    try:
        df = pd.read_csv(CSV_PATH)
        if df.empty or 'ts' not in df.columns or 'pnl_usd' not in df.columns: return 0.0
        df['ts'] = pd.to_datetime(df['ts'])
        tcut = pd.Timestamp.utcnow() - pd.Timedelta(hours=1)
        hr = df[df['ts']>=tcut]
        if hr.empty: return 0.0
        cum = hr['pnl_usd'].cumsum()
        dd = float((cum.cummax() - cum).max())
        return dd / max(1.0, NAV_USD) * 1e4
    except Exception:
        return 0.0

def run():
    loop = asyncio.get_event_loop()
    last_miss_alert = 0
    while True:
        try:
            for pair, cnt in check_drift_spike():
                reduce_risk()
                pause_pair(pair, PAUSE_MINUTES)
                loop.run_until_complete(send_webhook("warn", f"Drift spike {pair}: {cnt}/{DRIFT_WINDOW_MIN}m → paused {PAUSE_MINUTES}m"))
                loop.run_until_complete(send_tg(f"[Solbot] Drift spike {pair}: {cnt}/{DRIFT_WINDOW_MIN}m → paused {PAUSE_MINUTES}m"))
            age, miss = check_miss_slots()
            if miss >= MISS_SLOT_COUNT and time.time()-last_miss_alert>60:
                last_miss_alert = time.time()
                loop.run_until_complete(send_webhook("error", f"Miss slots: age={age}s, count={miss}"))
                loop.run_until_complete(send_tg(f"[Solbot] Miss slots: age={age}s, count={miss}"))
            dd = hourly_dd_bps()
            if dd >= HOURLY_DD_BPS:
                reduce_risk()
                loop.run_until_complete(send_webhook("error", f"Hourly DD {dd:.1f} bps > cap {HOURLY_DD_BPS}"))
                loop.run_until_complete(send_tg(f"[Solbot] Hourly DD {dd:.1f} bps > cap {HOURLY_DD_BPS}"))
        except Exception:
            pass
        time.sleep(5)

if __name__=='__main__':
    run()


# Auto-reduce size/priority on adverse signals
def reduce_risk():
    try:
        # reduce pf_mult and cu:mult by 10%, clamp by AUTO_SIZE_FACTOR_MIN
        pf = float((r.get('pf:mult') or b'1').decode())
        cu = float((r.get('cu:mult') or b'1').decode())
        pf = max(AUTO_SIZE_FACTOR_MIN, round(pf*0.9,3))
        cu = max(AUTO_SIZE_FACTOR_MIN, round(cu*0.9,3))
        r.set('pf:mult', str(pf)); r.set('cu:mult', str(cu))
    except Exception: pass
def global_pause(minutes:int=5):
    r.set('global:paused', str(int(__import__('time').time()) + minutes*60))
