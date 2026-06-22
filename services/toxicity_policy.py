
import os, time, json, redis, math, statistics

r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

def bayes(toxic_prior, ev_samples):
    # crude bayesian-ish update: toxic if large negative tails occur often
    if not ev_samples: return toxic_prior
    neg = [x for x in ev_samples if x<0]
    rate = (len(neg)/len(ev_samples))
    post = (toxic_prior*0.6 + rate*0.4)
    return max(0.0, min(1.0, post))

def main():
    print("[toxicity] running")
    prior=float(os.getenv("TOXIC_PRIOR","0.2"))
    while True:
        try:
            evs=[]; 
            for i in range(60):
                it=r.lindex("solbot:reconcile", i)
                if not it: break
                evs.append(json.loads(it).get("delta",0))
            score = bayes(prior, evs)
            r.setex("solbot:toxicity", 60, json.dumps({"score":score}))
            # Suggest fee/size policy
            tip_mult = 1.0 + score*0.2  # up to +20% tip if toxic
            size_mult = 1.0 - score*0.5 # reduce size up to -50% if highly toxic
            r.setex("solbot:toxicity:policy", 60, json.dumps({"tip_mult":round(tip_mult,3),"size_mult":round(size_mult,3)}))
        except Exception:
            pass
        time.sleep(5)

if __name__ == "__main__":
    main()
