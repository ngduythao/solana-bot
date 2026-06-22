
import os, time, redis
from cex_clients.binance_client import BINANCE_ENABLE, spot_ping as bin_ping
from cex_clients.bybit_client import BYBIT_ENABLE, server_time as byb_ping

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)

def run():
    while True:
        try:
            if BINANCE_ENABLE:
                r.hset("cex:health","binance", int(bin_ping()))
            if BYBIT_ENABLE:
                r.hset("cex:health","bybit", int(byb_ping()))
        except Exception as e:
            r.lpush("cex:err", str(e))
        time.sleep(5)

if __name__=="__main__":
    run()
