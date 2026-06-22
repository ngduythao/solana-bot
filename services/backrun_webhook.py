
from flask import Flask, request, jsonify
import os, redis, json, time
from services.common.secrets import load_system_env

load_system_env()
app = Flask(__name__)
r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

@app.route("/webhook/swap", methods=["POST"])
def swap_webhook():
    try:
        j = request.get_json(force=True) or {}
        # Expect shape similar to Helius swap event; store minimally
        ev = {
            "sig": j.get("signature") or j.get("txSignature"),
            "slot": j.get("slot"),
            "accounts": j.get("accounts", []),
            "program": j.get("program") or j.get("source","unknown"),
            "amountIn": j.get("amountIn"), "amountOut": j.get("amountOut"),
            "mintIn": j.get("mintIn"), "mintOut": j.get("mintOut"),
            "ts": time.time()
        }
        r.lpush("solbot:swap_events", json.dumps(ev)); r.ltrim("solbot:swap_events", 0, 999)
        # optional: trigger pre-sim hook by writing a key; other service reads it
        r.setex("solbot:swap:last", 30, json.dumps(ev))
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"ok":False,"err":str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("WEBHOOK_PORT","7080")))
