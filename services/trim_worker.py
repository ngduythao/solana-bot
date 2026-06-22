
import os, time, redis, shutil

r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
MAX_ALERTS = int(os.getenv("TRIM_MAX_ALERTS","1000"))
MAX_REPORT_MB = int(os.getenv("TRIM_MAX_REPORT_MB","20"))
MAX_LOG_MB = int(os.getenv("TRIM_MAX_LOG_MB","50"))
INTERVAL = int(os.getenv("TRIM_INTERVAL_SEC","60"))

def trim_redis_list(key, maxlen):
    llen = r.llen(key)
    if llen and llen>maxlen:
        r.ltrim(key, 0, maxlen-1)

def trim_file(path, max_mb):
    if not os.path.exists(path): return
    sz = os.path.getsize(path)/ (1024*1024)
    if sz <= max_mb: return
    # keep last 5 MB
    keep_mb = min(5, max_mb)
    with open(path,"rb") as f:
        f.seek(max(0, int(sz - keep_mb) * 1024*1024))
        data = f.read()
    with open(path,"wb") as f:
        f.write(data)

def walk_trim_dir(d, max_total_mb):
    total=0.0; files=[]
    if not os.path.isdir(d): return
    for fn in os.listdir(d):
        p=os.path.join(d,fn)
        if os.path.isfile(p):
            s=os.path.getsize(p)/(1024*1024)
            total+=s; files.append((p,s))
    if total>max_total_mb:
        # remove oldest first
        files.sort(key=lambda x: os.path.getmtime(x[0]))
        while total>max_total_mb and files:
            p,s=files.pop(0)
            try:
                os.remove(p); total-=s
            except: pass

def main():
    print("[trim_worker] running")
    while True:
        try:
            trim_redis_list("hsbot:alert_log", MAX_ALERTS)
            trim_file("logs/alerts.jsonl", MAX_LOG_MB)
            walk_trim_dir("reports", MAX_REPORT_MB)
        except Exception as e:
            pass
        time.sleep(INTERVAL)

if __name__=="__main__":
    main()
