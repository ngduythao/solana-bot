#!/usr/bin/env python3
# Lightweight EV filter combining rules + simple score (no heavy deps)
import os, math, json

def ev_filter(context: dict) -> dict:
    """
    context expects:
      route_ev (bps), slippage_bps, depth_ok (bool), recent_wr (%), latency_ms, tip_bps
    returns: {'accept': bool, 'score': float, 'reasons': []}
    """
    reasons=[]
    ev = float(context.get('route_ev', 0.0))
    sl = float(context.get('slippage_bps', 0.0))
    wr = float(context.get('recent_wr', 50.0))
    lat= float(context.get('latency_ms', 20.0))
    tip= float(context.get('tip_bps', 0.0))
    # Rules
    if sl > 80: reasons.append('slippage_high')
    if lat > 120: reasons.append('latency_high')
    if wr < 35: reasons.append('wr_low')
    # Score (normalized)
    score = (ev - 0.5*sl - 0.2*tip) + 0.1*(wr-50) - 0.05*max(0,lat-30)
    accept = (score > 0) and ('slippage_high' not in reasons)
    return {'accept': bool(accept), 'score': float(score), 'reasons': reasons}

if __name__=="__main__":
    import sys, json
    ctx=json.loads(sys.stdin.read() or "{}")
    print(json.dumps(ev_filter(ctx)))
