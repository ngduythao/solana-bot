
# WARNING: Scaffold only. Disabled by default. Do not expose on the internet.
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

ENABLED = os.getenv("SIGNER_ENABLED","0")=="1"
app = FastAPI()

class SignReq(BaseModel):
    message_b58: str

@app.post("/sign")
def sign(req: SignReq):
    if not ENABLED:
        raise HTTPException(403, "signer disabled")
    # TODO: load keypair & sign message; return signature b58
    return {"error":"not_implemented"}
