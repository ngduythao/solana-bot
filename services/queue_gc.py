
import os, time, redis
from services.common.logging_json import get_logger

log = get_logger("queue_gc")
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

LIMITS = {
    "autohedge:ix_req": 1000,
    "autohedge:cancel_req": 1000,
    "autohedge:sent": 500,
    "solbot:reconcile": 2000,
    "solbot:warnings": 500,
}

def main():
    log.info("queue_gc started")
    while True:
        try:
            for k, lim in LIMITS.items():
                n = r.llen(k) or 0
                if n and n > lim:
                    r.ltrim(k, 0, lim-1)
                    log.info(f"trim {k} from {n} -> {lim}")
        except Exception as e:
            log.error(f"gc error: {e}")
        time.sleep(2)

if __name__ == "__main__":
    main()
