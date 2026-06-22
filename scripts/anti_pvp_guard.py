#!/usr/bin/env python3
import os, sys, json, time, statistics
# Simple heuristic guard: tip spike or slot crowding -> return nonzero exit code to SKIP
# Inputs (env or args): PAIR, SLOT, TIP, WINDOW_MEDIAN_TIP
pair=os.environ.get("PAIR", "")
slot=int(os.environ.get("SLOT","0") or 0)
tip=float(os.environ.get("TIP","0") or 0.0)
median=float(os.environ.get("WINDOW_MEDIAN_TIP","0") or 0.0)
crowd=int(os.environ.get("SLOT_PAIR_COUNT","0") or 0)
reasons=[]
if median>0 and tip>2.0*median:
    reasons.append("tip_spike")
if crowd>=3:
    reasons.append("slot_crowd")
if reasons:
    print(json.dumps({"skip": True, "reasons": reasons, "pair": pair, "slot": slot, "tip": tip, "median": median, "crowd": crowd}))
    sys.exit(1)
print(json.dumps({"skip": False}))
