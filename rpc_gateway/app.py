
import os, json, httpx, redis
from fastapi import FastAPI, Request, Response

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)
DEFAULT=os.getenv("RPC_PRIMARY_FALLBACK","https://api.mainnet-beta.solana.com")
app=FastAPI(title="RPC Gateway")

def active_url():
    url = r.get("rpc:active_url")
    if url:
        try: return url.decode('utf-8')
        except Exception: return str(url)
    return os.getenv("RPC_PRIMARY", DEFAULT)

@app.post("/")
async def root_proxy(req: Request):
    body = await req.body()
    url = active_url()
    try:
        async with httpx.AsyncClient(timeout=2.5) as c:
            resp = await c.post(url, content=body, headers={"content-type":"application/json"})
        return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type","application/json"))
    except Exception as e:
        return Response(content=json.dumps({"error": str(e)}), status_code=502, media_type="application/json")
