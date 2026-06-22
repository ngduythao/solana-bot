
import os, httpx

ALERT_WEBHOOK = os.getenv("ALERT_WEBHOOK","")

async def alert(level: str, msg: str, extra: dict=None):
    if not ALERT_WEBHOOK: 
        return
    try:
        payload = {"level": level, "message": msg, "extra": extra or {}}
        async with httpx.AsyncClient(timeout=2.0) as c:
            await c.post(ALERT_WEBHOOK, json=payload)
    except Exception:
        pass
