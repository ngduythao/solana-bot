
import os, time, json, redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
KEY_PATH=os.getenv("SIGNER_KEY_PATH","/run/secrets/solana_keypair_hex")
RATE_QPS=float(os.getenv("SIGNER_RATE_QPS","20"))

r=redis.from_url(REDIS_URL)
app=FastAPI(title="Solana Bot Signer")

class SignReq(BaseModel):
    messages: List[str]

_last=0.0
def ratelimit():
    global _last
    now=time.time()
    min_dt=1.0/max(RATE_QPS,1e-3)
    if now-_last<min_dt:
        time.sleep(min_dt-(now-_last))
    _last=time.time()

def load_key()->SigningKey:
    if not os.path.exists(KEY_PATH):
        raise FileNotFoundError("missing SIGNER key secret")
    with open(KEY_PATH,"r") as f:
        key_hex=f.read().strip()
    return SigningKey(key_hex, encoder=HexEncoder)

@app.post("/sign")
def sign(req: SignReq):
    ratelimit()
    try:
        sk=load_key()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    sigs=[]
    for mhex in req.messages:
        try:
            msg=bytes.fromhex(mhex)
            sig=sk.sign(msg).signature.hex()
            sigs.append(sig)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"bad message: {e}")
    return {"sigs": sigs}
