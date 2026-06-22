
import os, time, json, hashlib, redis, glob, httpx

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)
BOT=os.getenv("TELEGRAM_BOT_TOKEN","")
CHAT=os.getenv("TELEGRAM_CHAT_ID","")

WATCH=list(filter(None, os.getenv("SEAL_PATHS","").split(",")))
if not WATCH:
    WATCH=[
        "services/*.py","deploy/*.sh","strategy/strategy.yaml",
        "/etc/solbot/.env"
    ]

STATE="/etc/solbot/SEAL.json"

def sha256_file(p):
    try:
        with open(p,"rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def send(msg):
    if not BOT or not CHAT: return
    try:
        with httpx.Client(timeout=3) as c:
            c.post(f"https://api.telegram.org/bot{BOT}/sendMessage", json={"chat_id": CHAT, "text": msg})
    except Exception: pass

def snapshot():
    m={}
    for pat in WATCH:
        for p in glob.glob(pat):
            h=sha256_file(p)
            if h: m[p]=h
    return m

def main():
    print("[runtime_seal] running")
    last={}
    if os.path.exists(STATE):
        try: last=json.load(open(STATE))
        except Exception: last={}
    else:
        cur=snapshot(); os.makedirs(os.path.dirname(STATE), exist_ok=True); json.dump(cur, open(STATE,"w"))
        last=cur
    while True:
        try:
            cur=snapshot()
            tamper=[]
            for k,v in cur.items():
                if k not in last or last[k]!=v:
                    tamper.append(k)
            if tamper:
                r.setex("solbot:kill:all", 180, "1")
                send("[SEAL] Detected changes: "+", ".join(tamper))
                json.dump(cur, open(STATE,"w"))
                last=cur
        except Exception: pass
        time.sleep(2)

if __name__=="__main__":
    main()
