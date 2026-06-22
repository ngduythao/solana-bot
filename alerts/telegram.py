
import os, requests

def _env(k, d=""):
    return os.environ.get(k) or _read_dotenv(k, d)

def _read_dotenv(k, d=""):
    try:
        with open(".env","r") as f:
            for line in f:
                if "=" in line:
                    kk, vv = line.strip().split("=",1)
                    if kk==k: return vv
    except Exception:
        pass
    return d

def send_alert(text: str):
    token=_env("TELEGRAM_BOT_TOKEN","").strip()
    chats=_env("TELEGRAM_CHAT_IDS","").strip()
    if not token or not chats: 
        return False
    for chat in [c.strip() for c in chats.replace(","," ").split() if c.strip()]:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat, "text": text[:3900]} , timeout=2.5)
        except Exception:
            pass
    return True
