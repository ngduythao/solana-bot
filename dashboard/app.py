
import os, secrets
from flask import Flask, render_template, redirect, url_for, request, flash
import redis

REDIS_URL = os.getenv("REDIS_URL","redis://redis:6379/0")
r = redis.from_url(REDIS_URL)

app = Flask(__name__)
app.secret_key = os.getenv("DASH_SECRET") or secrets.token_hex(32)

def get_state():
    st = {
        "paused": r.hget("ops_guard:state","paused"),
        "size_mult": r.hget("ops_guard:state","size_mult"),
        "bundle_accept_rate": r.get("bundle:accept_rate"),
        "p95": r.get("rpc:best_p95"),
        "pnl_day": r.get("hb:pnl:day"),
        "fee_burn": r.get("hb:fee_burn:day"),
        "inventory_skew_pct": r.get("hb:inventory_skew_pct"),
    }
    # decode
    for k,v in list(st.items()):
        if v is None: st[k]=None
        else:
            try: st[k]=float(v)
            except: st[k]=v.decode("utf-8") if isinstance(v,bytes) else v
    return st

@app.route("/")
def home():
    st = get_state()
    return render_template("index.html", st=st)

@app.route("/run", methods=["POST"])
def run():
    r.hset("ops_guard:state","paused",0)
    r.hset("ops_guard:state","size_mult",1.0)
    r.set("hb:control","run")
    flash("Bot RUN: paused=0, size_mult=1.0","success")
    return redirect(url_for("home"))

@app.route("/stop", methods=["POST"])
def stop():
    r.hset("ops_guard:state","paused",1)
    r.set("hb:control","stop")
    flash("Bot STOP: paused=1","warning")
    return redirect(url_for("home"))

@app.route("/restart", methods=["POST"])
def restart():
    # Soft restart signal for orchestrator to reload configs
    r.set("hb:control","restart")
    flash("Bot RESTART signal sent","info")
    return redirect(url_for("home"))

@app.route("/apply_best_rpc", methods=["POST"])
def apply_best_rpc():
    best = r.get("rpc:best_endpoint")
    if best:
        r.set("rpc:active_endpoint", best)
        flash(f"Applied best RPC: {best.decode('utf-8') if isinstance(best,bytes) else best}","success")
    else:
        flash("No benchmarked RPC found.","error")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
