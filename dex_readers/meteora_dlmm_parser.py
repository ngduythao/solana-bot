
"""Meteora DLMM parser — uses official @meteora-ag/dlmm SDK (Node)."""
import json, subprocess, os
from dataclasses import dataclass
from typing import List

@dataclass
class Bin:
    price_x64: int
    liq: int

@dataclass
class DlmmState:
    base_fee_bps: int
    bins: List[Bin]

def parse_dlmm_account_via_sdk(pool_pubkey:str) -> DlmmState:
    cmd = ["node","sdk/read_meteora_dlmm.js", pool_pubkey]
    env = os.environ.copy()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if p.returncode!=0:
        raise RuntimeError(p.stderr.strip() or "meteora sdk reader failed")
    d = json.loads(p.stdout.strip())
    bins = [Bin(price_x64=int(b["price_x64"]), liq=int(b["liq"])) for b in d.get("bins",[])]
    return DlmmState(base_fee_bps=int(d.get("base_fee_bps",30)), bins=bins)


import base64, yaml

def _le(b: bytes) -> int:
    return int.from_bytes(b, "little", signed=False)

def parse_dlmm_account_raw(data_b64: str) -> DlmmState:
    cfg = yaml.safe_load(open("config/layouts.yaml"))["meteora_dlmm"]
    raw = base64.b64decode(data_b64)
    head = cfg["head"]; binl = cfg["bin"]
    def head_get(k):
        off = int(head[k]["off"]); sz = int(head[k]["size"])
        if off+sz>len(raw): return 0
        return _le(raw[off:off+sz])
    base_fee_bps = head_get("base_fee_bps")
    bin_size = int(binl["size"])
    bins = []
    start = max(v["off"]+v["size"] for v in head.values())
    for i in range(0, 512):  # safety cap 512 bins
        off = start + i*bin_size
        if off+bin_size>len(raw): break
        p = _le(raw[off+binl["price_x64"]["off"]: off+binl["price_x64"]["off"]+binl["price_x64"]["size"]])
        q = _le(raw[off+binl["liq"]["off"]: off+binl["liq"]["off"]+binl["liq"]["size"]])
        bins.append(Bin(price_x64=p, liq=q))
    return DlmmState(base_fee_bps=base_fee_bps, bins=bins)

def parse_dlmm_account(pool_pubkey_or_b64: str, mode: str = None) -> DlmmState:
    mode = (mode or os.getenv("METEORA_PARSER_MODE","sdk")).lower()
    if mode == "sdk":
        return parse_dlmm_account_via_sdk(pool_pubkey_or_b64)
    else:
        return parse_dlmm_account_raw(pool_pubkey_or_b64)
