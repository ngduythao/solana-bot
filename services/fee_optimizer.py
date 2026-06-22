
# Simple fee optimizer stub
def choose_priority_fee(ev_bps: float, congestion: float) -> int:
    base = 8000
    return int(base * (1.0 + min(max(congestion,0.0),1.0)))
