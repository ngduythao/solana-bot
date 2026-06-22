import os, time, redis
r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
BASE=int(os.getenv("SIZE_NAV_BPS_BASE","50")); MIN_=int(os.getenv("SIZE_NAV_BPS_MIN","10")); MAX_=int(os.getenv("SIZE_NAV_BPS_MAX","200"))
def clamp(x,a,b): return max(a, min(b, x))
def main():
    cur=BASE
    while True:
        hit=float(r.get('hsbot:stats:hit_window') or 0); miss=float(r.get('hsbot:stats:miss_window') or 0)
        fr = miss/max(1.0, hit+miss); acc=float(r.get('hsbot:bundle:accepted_window') or 0); rej=float(r.get('hsbot:bundle:rejected_window') or 0)
        br = rej/max(1.0, acc+rej); panic=int(r.get('hsbot:panic') or 0); pause=int(r.get('hsbot:pause') or 0)
        if panic or pause: cur = MIN_
        else:
            if fr>0.15 or br>0.20: cur = max(MIN_, int(cur*0.7))
            else: cur = min(MAX_, int(cur*1.05))
        r.set('hsbot:cfg:size_nav_bps_override', cur); time.sleep(5)
if __name__=='__main__': main()
