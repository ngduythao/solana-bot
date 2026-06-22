import math, numpy as np
class Ranker:
    def __init__(self, thr=0.65): self.thr = thr
    def prob(self, ev_bps, impact_bps, hops, spread_bps=0.0):
        z = 0.5*ev_bps - 0.25*impact_bps - 0.1*hops - 0.05*spread_bps
        return 1/(1+math.exp(-z/3.0))
    def accept(self, pwin, pnl_per_sec): return (pwin >= self.thr) and pnl_per_sec>0
class FeeBidder:
    def __init__(self, max_pct_ev=0.18, max_lamports=22_000): self.max_pct_ev=max_pct_ev; self.max_lamports=max_lamports
    def cu_hint(self, ev_bps): return 350_000 + int(min(600_000, ev_bps*18_000))
    def micro_lamports(self, ev_bps):
        base = max(8, int(ev_bps*90)); cap = int(ev_bps*100*self.max_pct_ev); return min(base, cap, self.max_lamports)
class Scheduler:
    def __init__(self, boost_hours=None, deboost_hours=None): self.boost=set(boost_hours or []); self.deboost=set(deboost_hours or [])
    def boost_factor(self, hour): return 1.15 if hour in self.boost else (0.85 if hour in self.deboost else 1.0)
