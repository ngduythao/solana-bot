
from flask import Flask, Response, jsonify
import os, redis, time, json
from services.common.logging_json import get_logger

app = Flask(__name__)
log = get_logger("health")
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

@app.route("/live")
def live():
    return "OK", 200

@app.route("/ready")
def ready():
    try:
        r.ping()
        return "READY", 200
    except Exception as e:
        log.error(f"redis not ready: {e}")
        return "NOT_READY", 503

@app.route("/metrics")
def metrics():
    # minimal metrics snapshot from redis keys
    try:
        acc = 0.0; relays=0
        for k in r.scan_iter(match="jito:relay_stats:*"):
            kd=k.decode()
            if kd.endswith(":leaders"): continue
            h=r.hgetall(k)
            cnt=int(h.get(b"count",b"0") or 0); suc=int(h.get(b"success",b"0") or 0)
            if cnt>0: acc += suc/cnt; relays+=1
        acc = (acc/relays) if relays>0 else 0.0
    except Exception:
        acc = 0.0
    lines = [
        f"solbot_accept_ratio {acc}",
        f"solbot_queue_autohedge_ix_req {int(r.llen('autohedge:ix_req') or 0)}",
        f"solbot_queue_autohedge_cancel {int(r.llen('autohedge:cancel_req') or 0)}",
        f"solbot_reconcile_len {int(r.llen('solbot:reconcile') or 0)}",
    ]
    return Response("\n".join(lines)+"\n", mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("HEALTH_PORT","9090")))
