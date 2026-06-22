import os, time, json, random, redis
r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
EPS=float(os.getenv("AI_BANDIT_EPS","0.1"))
ACTIONS=[0.8, 1.0, 1.2, 1.4]
def key(ctx): return "hsbot:bandit:" + "|".join(str(ctx.get(k)) for k in ["hr","pair","route","rpcb"])
def pick(ctx):
    import random
    if random.random()<EPS: return random.choice(ACTIONS)
    k=key(ctx); best=None; bestv=-1e9
    for a in ACTIONS:
        try: v=float(r.hget(k, str(a)) or 0.0)
        except: v=0.0
        if v>bestv: best, bestv=a, v
    return best or 1.0
def update(ctx, action, reward):
    k=key(ctx); cur=float(r.hget(k, str(action)) or 0.0); r.hset(k, str(action), cur*0.99 + reward*0.01)
def main():
    while True: time.sleep(5)
if __name__=="__main__": main()
