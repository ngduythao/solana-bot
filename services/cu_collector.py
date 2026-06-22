import os, time, json, redis, requests
r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
RPC = os.getenv("HELIUS_RPC") or os.getenv("RPC_PRIMARY","https://api.mainnet-beta.solana.com")
def get_tx(tx):
    try:
        resp = requests.post(RPC, json={"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[tx, {"encoding":"json","maxSupportedTransactionVersion":0}]}, timeout=3)
        if resp.status_code==200: return resp.json()
    except Exception: return None
def main():
    while True:
        tx = r.lpop("hsbot:recent_tx")
        if not tx: time.sleep(1); continue
        try:
            tx=tx.decode(); j=get_tx(tx); 
            if not j: continue
            meta=(j.get("result") or {}).get("meta") or {}
            cu = meta.get("computeUnitsConsumed")
            if cu is not None:
                r.lpush("hsbot:cu_log", json.dumps({"ts": time.time(), "tx": tx, "cu": cu}))
                r.set("hsbot:last_cu", cu)
        except Exception: pass
if __name__=="__main__": main()
