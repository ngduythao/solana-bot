from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, JSONResponse
import subprocess, shlex

app = FastAPI(title="Solbot Control", version="1.0")

HTML = """
<!doctype html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Solbot Control</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,sans-serif;margin:24px;max-width:800px}
h1{margin:0 0 12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:12px 0 24px}
.btn{padding:12px 16px;border-radius:10px;border:1px solid #ddd;background:#f7f7f7;cursor:pointer;font-weight:600}
.btn:hover{background:#eee}
pre{background:#0b1020;color:#e7edf5;padding:12px;border-radius:10px;overflow:auto}
.badge{display:inline-block;padding:4px 8px;border-radius:8px;background:#eee;font-weight:600}
.badge.ok{background:#d1fae5}
.badge.bad{background:#fee2e2}
</style>
<script>
async function call(act){
  const r = await fetch('/api/control/'+act,{method:'POST'});
  const j = await r.json();
  document.getElementById('out').textContent = JSON.stringify(j,null,2);
  await refresh();
}
async function refresh(){
  const r = await fetch('/api/control/status');
  const j = await r.json();
  const el = document.getElementById('status');
  el.textContent = j.status;
  el.className = 'badge ' + (j.status==='active'?'ok':'bad');
}
window.addEventListener('load', refresh);
</script>
</head><body>
<h1>Solbot Control (local)</h1>
<div>Service: <span id="status" class="badge">...</span></div>
<div class="grid">
  <button class="btn" onclick="call('restart')">Restart</button>
  <button class="btn" onclick="call('start')">Start</button>
  <button class="btn" onclick="call('stop')">Stop</button>
  <a class="btn" href="http://127.0.0.1:8080/" target="_blank" rel="noopener">Open Panel</a>
</div>
<pre id="out">Ready.</pre>
</body></html>
"""

def _run(cmd: str) -> tuple[int,str,str]:
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate(timeout=30)
    return p.returncode, out.strip(), err.strip()

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML

@app.get("/api/control/status")
def status():
    code, out, err = _run("systemctl is-active solbot-all.service")
    st = out if out else "unknown"
    return JSONResponse({"ok": code == 0, "status": st, "err": err})

@app.post("/api/control/restart")
def restart():
    code, out, err = _run("systemctl restart solbot-all.service")
    return JSONResponse({"ok": code == 0, "out": out, "err": err})

@app.post("/api/control/start")
def start():
    code, out, err = _run("systemctl start solbot-all.service")
    return JSONResponse({"ok": code == 0, "out": out, "err": err})

@app.post("/api/control/stop")
def stop():
    code, out, err = _run("systemctl stop solbot-all.service")
    return JSONResponse({"ok": code == 0, "out": out, "err": err})
