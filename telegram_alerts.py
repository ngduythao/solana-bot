
import os, httpx, asyncio

TG_TOKEN = os.getenv("ALERT_TG_TOKEN","")
TG_CHAT  = os.getenv("ALERT_TG_CHAT","")

async def tg_alert(text: str):
    if not TG_TOKEN or not TG_CHAT: return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT, "text": text[:4000], "disable_web_page_preview": True}
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            await c.post(url, json=data)
    except Exception:
        pass
