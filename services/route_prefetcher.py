import os, time, csv, json, redis
from datetime import datetime
r = redis.from_url(os.getenv('REDIS_URL','redis://redis:6379/0'))
def bucket_hour(ts): return datetime.utcfromtimestamp(float(ts)).strftime('%H')
def main():
    while True:
        try:
            if not os.path.exists('logs/executions.csv'): time.sleep(10); continue
            wins={}
            with open('logs/executions.csv','r') as f:
                for row in csv.DictReader(f):
                    route=row.get('route_label') or 'unknown'
                    gross=float(row.get('pnl_gross','0') or 0)-(float(row.get('priority_fee','0') or 0)+float(row.get('rpc_fee','0') or 0))
                    ts=float(row.get('ts_submit','0') or row.get('ts_detect','0') or 0)
                    if ts<=0: continue
                    hr=bucket_hour(ts); wins[(hr,route)]=wins.get((hr,route),0.0)+gross
            per={}
            for (h,route),val in wins.items():
                per.setdefault(h,[]).append((route,val))
            for h,arr in per.items():
                arr.sort(key=lambda x:x[1], reverse=True); r.delete(f'hsbot:route_bias:{h}')
                for route,_ in arr[:10]: r.rpush(f'hsbot:route_bias:{h}', route)
        except Exception: pass
        time.sleep(30)
if __name__=='__main__': main()
