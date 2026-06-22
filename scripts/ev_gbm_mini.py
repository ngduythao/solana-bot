#!/usr/bin/env python3
import json, math, sys

def gbm_score(ctx):
    # Simple additive model of decision stumps; weights tuned heuristically
    ev = float(ctx.get('route_ev', 0.0))
    sl = float(ctx.get('slippage_bps', 0.0))
    wr = float(ctx.get('recent_wr', 50.0))
    lat= float(ctx.get('latency_ms', 20.0))
    tip= float(ctx.get('tip_bps', 0.0))
    s = 0.0
    # Trees / stumps
    s += 0.8 if ev > 15 else (-0.6 if ev < 5 else 0.2)
    s += -0.9 if sl > 60 else (0.2 if sl < 20 else -0.2)
    s += 0.6 if wr > 55 else (-0.6 if wr < 40 else 0.0)
    s += -0.5 if lat > 120 else (0.2 if lat < 40 else -0.1)
    s += -0.3 if tip > 20 else 0.0
    # convert to prob via sigmoid
    prob = 1/(1+math.exp(-s))
    return prob, s

def decide(ctx):
    prob, raw = gbm_score(ctx)
    ev = float(ctx.get('route_ev',0.0))
    risk = float(ctx.get('risk_bps', 8.0))  # impact + variance proxy
    # net EV bps estimate
    net = prob*ev - 0.5*risk
    return {'accept': net>0, 'prob': prob, 'raw': raw, 'net_bps': net}

if __name__=='__main__':
    ctx=json.loads(sys.stdin.read() or "{}")
    print(json.dumps(decide(ctx)))
