
import os, time, json, redis, datetime as dt
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
# Default daily budgets
B_TIP=int(os.getenv("BUDGET_TIP_LAMPORTS","250000000"))
B_FEE=float(os.getenv("BUDGET_DEX_FEE","80"))
B_SLIP=float(os.getenv("BUDGET_SLIP_BPS","1200"))

def day_key(prefix):
    today=dt.date.today().isoformat()
    return f"{prefix}:{today}"

def main():
    print("[budget_planner] running")
    while True:
        try:
            k_tip=day_key("budget:tip"); k_fee=day_key("budget:fee"); k_slip=day_key("budget:slip")
            # init if not exists
            r.setnx(k_tip, B_TIP); r.setnx(k_fee, B_FEE); r.setnx(k_slip, B_SLIP)
            # read consumed (guard service keeps sums)
            tip=int(r.get("solbot:sum:tip") or 0); fee=float(r.get("solbot:sum:fee") or 0.0); slip=float(r.get("solbot:sum:slip") or 0.0)
            rem={"tip":max(0,int(r.get(k_tip))-tip), "fee":max(0,float(r.get(k_fee))-fee), "slip":max(0,float(r.get(k_slip))-slip)}
            r.setex("solbot:budget:remaining", 30, json.dumps(rem))
        except Exception: pass
        time.sleep(5)

if __name__=="__main__":
    main()
