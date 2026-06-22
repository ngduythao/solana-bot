
import os, time, json, pickle, redis, math, statistics

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)
MODEL_PATH=os.getenv("EV_MODEL_PATH","/etc/solbot/ev_model.pkl")

def bayes_pr(ev_samples):
    if not ev_samples: return 0.5
    neg=sum(1 for x in ev_samples if x<0); n=len(ev_samples)
    prior=0.5
    return (prior*0.6 + (neg/n)*0.4)

def feat_from_ctx(ctx:dict):
    # Minimal feature set; extend as needed
    return [
        float(ctx.get("tip_floor", 0)),
        float(ctx.get("lat_p50", 0)),
        float(ctx.get("lat_p95", 0)),
        float(ctx.get("accept_rate", 0)),
        float(ctx.get("size_q0", 0))/1e6,
        float(ctx.get("fee_bps", 30)),
        float(ctx.get("hour", 0))
    ]

def predict(ctx:dict):
    # Bayes + (optional) lightgbm-style model
    try:
        with open(MODEL_PATH, "rb") as f:
            mdl=pickle.load(f)
    except Exception:
        mdl=None
    # bayes branch from recent reconcile
    evs=[]; 
    for i in range(60):
        it=r.lindex("solbot:reconcile", i)
        if not it: break
        evs.append(int(json.loads(it).get("delta",0)))
    bay = 1.0 - bayes_pr(evs)
    if mdl is None:
        return {"p_win": bay, "src": "bayes"}
    # simple linear/gbm-like predict_proba
    try:
        x=[feat_from_ctx(ctx)]
        p = float(mdl.predict_proba(x)[0][1]) if hasattr(mdl,"predict_proba") else float(mdl.predict(x)[0])
        return {"p_win": 0.5*p + 0.5*bay, "src": "ensemble"}
    except Exception:
        return {"p_win": bay, "src": "bayes"}

def main():
    print("[ai_ev] running")
    while True:
        try:
            # read latest context (best-effort)
            ctx = json.loads(r.get("solbot:ctx:last") or b"{}")
            pred = predict(ctx)
            r.setex("solbot:ev_pred", 30, json.dumps(pred))
            # suggest policy: map p_win -> tip/size multipliers
            tip_mult = 1.0 + max(0.0, (0.7 - pred["p_win"])) * 0.3
            size_mult = 0.5 + pred["p_win"] * 0.7  # 0.5..1.2x
            r.setex("solbot:ev_policy", 30, json.dumps({"tip_mult":round(tip_mult,3),"size_mult":round(size_mult,3)}))
        except Exception:
            pass
        time.sleep(2)

if __name__=="__main__":
    main()
