
import os, time, redis, json
from dotenv import load_dotenv
load_dotenv()
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)

RPCS = [s.strip() for s in os.getenv("RPC_FALLBACKS","https://api.mainnet-beta.solana.com").split(",") if s.strip()]
PRIMARY = os.getenv("RPC_PRIMARY","https://api.mainnet-beta.solana.com")

def run():
    last=PRIMARY
    r.set("rpc:current", last)
    while True:
        for rpc in [PRIMARY] + RPCS:
            r.set("rpc:current", rpc)
            time.sleep(10)

if __name__=="__main__":
    run()
