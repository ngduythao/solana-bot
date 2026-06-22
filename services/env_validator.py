
import os, time, redis, json

REQUIRED = [
  "REDIS_URL", "RPC_PRIMARY",
]
OPTIONAL = ["JITO_RELAYS", "TIP_STREAM_URL"]
def main():
    print("[env_validator] checking...")
    missing=[k for k in REQUIRED if not os.getenv(k)]
    if missing:
        print("[env_validator] missing:", missing)
    else:
        print("[env_validator] OK")
    # write a status key
    try:
        r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
        r.setex("solbot:env:ok", 60, json.dumps({"ok": len(missing)==0, "missing": missing}))
    except Exception:
        pass
    time.sleep(1)

if __name__ == "__main__":
    main()
