
import os, json, csv, redis
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
REDIS_URL = os.getenv("REDIS_URL","redis://redis:6379/0")
r = redis.from_url(REDIS_URL)

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(os.path.dirname(BASE),"dashboard")

app.mount("/static", StaticFiles(directory=STATIC), name="static")

@app.get("/", response_class=HTMLResponse)
def root():
    return FileResponse(os.path.join(STATIC,"index.html"))

@app.get("/api/failcause")
def failcause():
    keys = ["stale","slippage","whitelist","no_route","unknown"]
    out = {k:int(r.get(f"hsbot:failcause:{k}") or 0) for k in keys}
    return JSONResponse(out)

@app.get("/api/pnl_hourly")
def pnl_hourly():
    path = os.path.join(os.path.dirname(BASE),"reports","pnl_hourly.csv")
    rows=[]; 
    if os.path.exists(path):
        with open(path,"r") as f:
            rows = list(csv.DictReader(f))
    return JSONResponse(rows)

@app.get("/api/pnl_daily")
def pnl_daily():
    path = os.path.join(os.path.dirname(BASE),"reports","pnl_daily.csv")
    rows=[]; 
    if os.path.exists(path):
        with open(path,"r") as f:
            rows = list(csv.DictReader(f))
    return JSONResponse(rows)

@app.get("/api/acceptance")
def acceptance():
    # Expect per-relay counters hsbot:bundle:accepted:<relay>, rejected:<relay>
    relays = (os.getenv("JITO_RELAYS","").split(",") if os.getenv("JITO_RELAYS") else [])
    out=[]
    for rl in relays:
        rl=rl.strip()
        if not rl: continue
        acc = int(r.get(f"hsbot:bundle:accepted:{rl}") or 0)
        rej = int(r.get(f"hsbot:bundle:rejected:{rl}") or 0)
        out.append({"relay": rl, "accepted": acc, "rejected": rej})
    return JSONResponse(out)


@app.get("/api/latency")
def latency():
    # read last N latency events and compute p50/p95
    vals=[]
    for raw in r.lrange("hsbot:lat_events", 0, 2000):
        try:
            ev=json.loads(raw)
            if ev.get("ts_detect") and ev.get("ts_submit"):
                ms=(float(ev["ts_submit"])-float(ev["ts_detect"])) * 1000.0
                vals.append(ms)
        except: pass
    vals=sorted(vals)
    if not vals:
        return JSONResponse({"p50": None, "p95": None, "count": 0})
    import statistics, math
    p50=statistics.median(vals)
    p95=vals[max(0, int(0.95*len(vals))-1)]
    return JSONResponse({"p50": round(p50,2), "p95": round(p95,2), "count": len(vals)})

@app.get("/api/inventory")
def inventory():
    tokens = ["USDC","SOL","JUP","BONK","WIF"]
    out=[]
    for t in tokens:
        bal = float(r.get(f"hsbot:bal:{t}") or 0.0)
        px = float(r.get(f"hsbot:price:{t}") or (1.0 if t!="SOL" else 150.0))
        usd = bal*px
        out.append({"token": t, "balance": bal, "price": px, "usd": usd})
    # compute total NAV approximation
    nav = sum(x["usd"] for x in out)
    for x in out:
        x["pct_nav"] = round((x["usd"]/nav*100.0), 4) if nav>0 else 0.0
    return JSONResponse({"nav": nav, "list": out})

@app.get("/api/alerts")
def alerts():
    # Return last 100 alert entries from Redis list
    items=[]
    for raw in r.lrange("hsbot:alert_log", 0, 100):
        try:
            items.append(json.loads(raw))
        except:
            pass
    return JSONResponse(items[::-1])


@app.get("/api/latency_detailed")
def latency_detailed():
    # Expect events with ts_detect, ts_sim, ts_submit in hsbot:lat_events
    det_sim=[]; sim_sub=[]; det_sub=[]
    for raw in r.lrange("hsbot:lat_events", 0, 2000):
        try:
            e=json.loads(raw)
            td=e.get("ts_detect"); ts=e.get("ts_sim"); tb=e.get("ts_submit")
            if td and ts: det_sim.append( (float(ts)-float(td))*1000.0 )
            if ts and tb: sim_sub.append( (float(tb)-float(ts))*1000.0 )
            if td and tb: det_sub.append( (float(tb)-float(td))*1000.0 )
        except: pass
    def stats(arr):
        if not arr: return {"p50":None,"p95":None,"n":0}
        arr=sorted(arr)
        import statistics
        p50=statistics.median(arr)
        p95=arr[max(0,int(0.95*len(arr))-1)]
        return {"p50":round(p50,2),"p95":round(p95,2),"n":len(arr)}
    return JSONResponse({
        "detect_to_sim": stats(det_sim),
        "sim_to_submit": stats(sim_sub),
        "detect_to_submit": stats(det_sub),
    })


@app.get("/api/latency_series")
def latency_series():
    # Return last N=300 events as timeseries for detect->sim, sim->submit, detect->submit
    N = int(os.getenv("LAT_SERIES_N","300"))
    det_sim=[]; sim_sub=[]; det_sub=[]
    for raw in r.lrange("hsbot:lat_events", 0, N):
        try:
            e=json.loads(raw)
            td=e.get("ts_detect"); ts=e.get("ts_sim"); tb=e.get("ts_submit")
            t=e.get("ts_submit") or e.get("ts_sim") or e.get("ts_detect")
            if not t: continue
            t=float(t)
            if td and ts: det_sim.append([t, (float(ts)-float(td))*1000.0])
            if ts and tb: sim_sub.append([t, (float(tb)-float(ts))*1000.0])
            if td and tb: det_sub.append([t, (float(tb)-float(td))*1000.0])
        except: pass
    # sort by time
    det_sim.sort(key=lambda x:x[1] if len(x)>1 else 0)
    sim_sub.sort(key=lambda x:x[1] if len(x)>1 else 0)
    det_sub.sort(key=lambda x:x[1] if len(x)>1 else 0)
    return JSONResponse({"det_sim": det_sim, "sim_sub": sim_sub, "det_sub": det_sub})


@app.get("/api/rpc_breakdown")
def rpc_breakdown():
    # read configured primary/fallbacks and show EMA latency + error %
    primary = r.get("hsbot:cfg:rpc_primary")
    primary = primary.decode() if primary else os.getenv("RPC_PRIMARY") or os.getenv("HELIUS_RPC") or ""
    fall = [x.strip() for x in (os.getenv("RPC_FALLBACKS","").split(",") if os.getenv("RPC_FALLBACKS") else []) if x.strip()]
    urls = [u for u in [primary]+fall if u]
    out=[]
    for url in urls:
        lat = float(r.get(f"hsbot:rpc:lat_ms:{url}") or 0.0)
        ok = int(r.get(f"hsbot:rpc:ok:{url}") or 0)
        err = int(r.get(f"hsbot:rpc:err:{url}") or 0)
        total = ok+err if (ok+err)>0 else 1
        er = round(err*100.0/total,2)
        out.append({"url": url, "lat_ms": lat, "err_pct": er, "is_current": 1 if url==primary else 0})
    return JSONResponse(out)

@app.get("/api/route_pnl")
def route_pnl():
    # serve top-N route pnl/sec from reports/route_pnl_top.json if exists
    path = os.path.join(os.path.dirname(BASE),"reports","route_pnl_top.json")
    if os.path.exists(path):
        with open(path,"r") as f:
            try:
                data=json.load(f)
            except Exception:
                data=[]
        return JSONResponse(data)
    # fallback: compute roughly from executions.csv on the fly
    path2 = os.path.join(os.path.dirname(BASE),"logs","executions.csv")
    rows=[]
    if os.path.exists(path2):
        import csv, time
        with open(path2,"r") as f:
            for row in csv.DictReader(f):
                try:
                    route = row.get("route_label") or "unknown"
                    gross=float(row.get("pnl_gross","0") or 0)
                    fee=float(row.get("priority_fee","0") or 0)+float(row.get("rpc_fee","0") or 0)
                    tsd=float(row.get("ts_detect","0") or 0)
                    tss=float(row.get("ts_submit","0") or 0)
                    dur=max(0.001, tss-tsd)
                    pnlps=(gross-fee)/dur
                    rows.append({"route":route,"pnlps":pnlps,"gross":gross,"fee":fee,"dur":dur})
                except: pass
        rows=sorted(rows,key=lambda x: x["pnlps"], reverse=True)[:20]
    return JSONResponse(rows)

@app.get("/api/cu_stats")
def cu_stats():
    import json
    items=[]
    for raw in r.lrange("hsbot:cu_log", 0, 200):
        try:
            items.append(json.loads(raw))
        except: pass
    items = items[::-1]
    if not items:
        return JSONResponse({"avg": None, "last": None, "count": 0})
    avg = sum([x.get("cu",0) for x in items]) / max(1,len(items))
    last = items[-1].get("cu")
    return JSONResponse({"avg": round(avg,2), "last": last, "count": len(items)})

@app.get("/api/relay_acceptance")
def relay_acceptance():
    relays = (os.getenv("JITO_RELAYS","").split(",") if os.getenv("JITO_RELAYS") else [])
    out=[]
    for rl in relays:
        rl=rl.strip()
        if not rl: continue
        acc = int(r.get(f"hsbot:bundle:accepted:{rl}") or 0)
        rej = int(r.get(f"hsbot:bundle:rejected:{rl}") or 0)
        out.append({"relay": rl, "accepted": acc, "rejected": rej})
    return JSONResponse(out)
