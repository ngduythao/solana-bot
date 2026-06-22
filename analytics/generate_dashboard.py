
import os, csv, time, json, math
from datetime import datetime

METRICS_PATH = os.getenv("METRICS_PATH","metrics.csv")
OUT_DIR = os.path.join(os.getcwd(), "dashboard")
OUT_HTML = os.path.join(OUT_DIR, "index.html")
REFRESH_SEC = int(os.getenv("DASHBOARD_REFRESH_SEC","5"))
TAIL_N = int(os.getenv("DASHBOARD_TAIL_N","5000"))

def read_tail_csv(path, n):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            rows = f.readlines()
        head = rows[0]
        data = rows[-min(n, len(rows)-1):] if len(rows)>1 else []
        return [head] + data
    except FileNotFoundError:
        return []

def to_rows(lines):
    if not lines: return [], []
    reader = csv.DictReader(lines)
    rows = list(reader)
    # normalize fields
    out = []
    for r in rows:
        out.append({
            "ts": float(r.get("ts", time.time())),
            "route": (r.get("route_label") or r.get("route") or "UNKNOWN"),
            "lat_ms": float(r.get("latency_ms", r.get("lat_ms", 0)) or 0),
            "pnl": float(r.get("pnl_usd", r.get("pnl", 0)) or 0),
            "slip_bps": float(r.get("slip_bps", r.get("slippage_bps", 0)) or 0),
            "side": r.get("side","?"),
        })
    return rows, out

def summarize(out):
    if not out: return {}
    n=len(out)
    pnl=[x["pnl"] for x in out]
    lat=[x["lat_ms"] for x in out if x["lat_ms"]>0]
    win=sum(1 for x in pnl if x>0)
    total=sum(pnl)
    avg=(total/n) if n else 0.0
    p95 = sorted(lat)[int(0.95*len(lat))-1] if lat else 0.0
    routes={}
    for x in out:
        routes.setdefault(x["route"], {"n":0,"pnl":0.0,"lat":[]})
        routes[x["route"]]["n"]+=1
        routes[x["route"]]["pnl"]+=x["pnl"]
        if x["lat_ms"]>0: routes[x["route"]]["lat"].append(x["lat_ms"])
    for k,v in routes.items():
        v["p95"]=sorted(v["lat"])[int(0.95*len(v["lat"]))-1] if v["lat"] else 0.0
    return {"n":n,"win":win,"wr": (100.0*win/n) if n else 0.0, "pnl":total, "avg":avg, "p95":p95, "routes":routes}

def render_html(stats, out):
    os.makedirs(OUT_DIR, exist_ok=True)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    data_json = json.dumps(out)
    stats_json = json.dumps(stats)
    html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>solbot dashboard</title>
<meta http-equiv="refresh" content="{REFRESH_SEC}">
<style>
body {{ font-family: Arial, sans-serif; margin: 16px; }}
h1 {{ margin: 0 0 8px 0; }}
.card {{ border:1px solid #ddd; border-radius:12px; padding:12px; margin:8px 0; }}
.small {{ color:#666; font-size:12px; }}
table {{ width:100%; border-collapse:collapse; }}
th, td {{ border-bottom:1px solid #eee; padding:6px; text-align:left; }}
#chart {{ width: 100%; height: 260px; }}
</style>
</head>
<body>
<h1>solbot dashboard</h1>
<div class="small">updated: {now} — auto refresh {REFRESH_SEC}s</div>

<div class="card">
  <b>Summary (tail {TAIL_N} rows)</b>
  <div>Trades: <b>{stats.get("n",0)}</b> — Win: <b>{stats.get("win",0)}</b> — WR: <b>{stats.get("wr",0):.2f}%</b> — PnL: <b>${stats.get("pnl",0):.2f}</b> — p95 Latency: <b>{stats.get("p95",0):.1f} ms</b></div>
</div>

<div class="card">
  <b>Route PnL / p95 latency</b>
  <table>
    <tr><th>Route</th><th>Trades</th><th>PnL</th><th>p95 Lat (ms)</th></tr>
    {''.join(f"<tr><td>{k}</td><td>{v['n']}</td><td>{v['pnl']:.2f}</td><td>{v['p95']:.1f}</td></tr>" for k,v in stats.get("routes",{{}}).items())}
  </table>
</div>

<div class="card">
  <b>PnL timeline (last 500 pts)</b>
  <canvas id="chart"></canvas>
</div>

<script>
const data = {data_json};
const last = data.slice(-500);
const xs = last.map(x => new Date(x.ts*1000));
const ys = last.map(x => x.pnl);
const ctx = document.getElementById('chart').getContext('2d');

// Minimal chart without external libs
(function() {{
  const c = document.getElementById('chart');
  const w = c.width = c.clientWidth;
  const h = c.height = c.clientHeight;
  const minY = Math.min(...ys, 0);
  const maxY = Math.max(...ys, 0);
  const pad = 20;

  const cx = c.getContext('2d');
  cx.clearRect(0,0,w,h);
  cx.beginPath();
  cx.moveTo(0,h/2); cx.lineTo(w,h/2); cx.strokeStyle='#ddd'; cx.stroke();

  if (ys.length < 2) return;
  function normY(v) {{
    if (maxY===minY) return h/2;
    return h - ((v - minY) / (maxY - minY)) * h;
  }}
  const step = w / (ys.length - 1);
  cx.beginPath();
  cx.moveTo(0, normY(ys[0]));
  for (let i=1;i<ys.length;i++) {{
    cx.lineTo(i*step, normY(ys[i]));
  }}
  cx.strokeStyle='#333'; cx.lineWidth=1.5; cx.stroke();
}})();
</script>

</body></html>
"""
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    return OUT_HTML

def main():
    lines = read_tail_csv(METRICS_PATH, TAIL_N)
    _, out = to_rows(lines)
    stats = summarize(out)
    path = render_html(stats, out)
    print(path)

if __name__ == "__main__":
    main()
