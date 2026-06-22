#!/usr/bin/env python3
import os, time, redis

r=redis.Redis(host='localhost', port=6379, decode_responses=True)

def has_wallet_pubkey():
    try:
        if not os.path.exists(".env"): return False
        for line in open(".env"):
            if line.startswith("WALLET_PUBKEY="):
                return len(line.split("=",1)[1].strip())>24
        return False
    except Exception:
        return False

def has_encrypted_key():
    return os.path.exists("/opt/solbot/keys/id.json.gpg")

def has_any_rpc():
    try:
        if not os.path.exists(".env"): return False
        for line in open(".env"):
            if line.startswith("RPC_CANDIDATES="):
                return len(line.split("=",1)[1].strip())>0
        return False
    except Exception:
        return False

def main():
    while True:
        missing=[]
        if not has_wallet_pubkey(): missing.append("WALLET_PUBKEY")
        if not has_encrypted_key(): missing.append("GPG_KEY")
        if not has_any_rpc(): missing.append("RPC_CANDIDATES")
        if missing:
            r.set("hsbot:run:mode","dry", ex=300)
            r.set("hsbot:run:missing", ",".join(missing), ex=300)
        else:
            r.set("hsbot:run:mode","live", ex=300)
            r.delete("hsbot:run:missing")
        time.sleep(5)

if __name__=="__main__":
    main()
