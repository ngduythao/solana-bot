import os, redis
from flask import Flask, Response
app = Flask(__name__); r = redis.from_url(os.getenv('REDIS_URL','redis://redis:6379/0'))
def g(k, d=0.0):
    try: v=r.get(k); return float(v) if v else d
    except: return d
@app.route('/metrics')
def metrics():
    L=[]; L.append(f'solbot_hit_window {g("hsbot:stats:hit_window")}'); L.append(f'solbot_miss_window {g("hsbot:stats:miss_window")}')
    L.append(f'solbot_bundle_accepted_window {g("hsbot:bundle:accepted_window")}'); L.append(f'solbot_bundle_rejected_window {g("hsbot:bundle:rejected_window")}')
    L.append(f'solbot_pnl_today {g("hsbot:stats:gross_pnl_today")}'); L.append(f'solbot_pf_mult {g("hsbot:cfg:pf_mult",1.0)}')
    L.append(f'solbot_size_nav_bps {g("hsbot:cfg:size_nav_bps_override", g("SIZE_MAX_NAV_BPS",50))}')
    return Response("\n".join(L)+"\n", mimetype='text/plain')
