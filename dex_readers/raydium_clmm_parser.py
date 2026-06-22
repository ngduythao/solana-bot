
"""Raydium CLMM parser — uses official SDK v2 via Node to avoid manual offsets."""
import json, subprocess, os
from dataclasses import dataclass

@dataclass
class ClmmState:
    tick_spacing: int
    sqrt_price_x64: int
    liquidity: int
    fee_tier_bps: int

def parse_clmm_account_via_sdk(pool_pubkey:str) -> ClmmState:
    cmd = ["node","sdk/read_raydium_clmm.js", pool_pubkey]
    env = os.environ.copy()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if p.returncode!=0:
        raise RuntimeError(p.stderr.strip() or "raydium sdk reader failed")
    d = json.loads(p.stdout.strip())
    return ClmmState(
        tick_spacing = int(d.get("tickSpacing",0)),
        sqrt_price_x64 = int(d.get("sqrtPriceX64","0")),
        liquidity = int(d.get("liquidity","0")),
        fee_tier_bps = int(d.get("fee_bps",0))
    )


import base64, yaml

def _le(b: bytes) -> int:
    return int.from_bytes(b, "little", signed=False)

def parse_clmm_account_raw(data_b64: str) -> ClmmState:
    lay = yaml.safe_load(open("config/layouts.yaml"))["raydium_clmm"]
    raw = base64.b64decode(data_b64)
    def get(k):
        off = int(lay[k]["off"]); sz = int(lay[k]["size"])
        if off+sz>len(raw): return 0
        return _le(raw[off:off+sz])
    return ClmmState(
        tick_spacing = get("tick_spacing"),
        sqrt_price_x64 = get("sqrt_price_x64"),
        liquidity = get("liquidity"),
        fee_tier_bps = get("fee_tier_bps")
    )

def parse_clmm_account(pool_pubkey_or_b64: str, mode: str = None) -> ClmmState:
    mode = (mode or os.getenv("RAYDIUM_PARSER_MODE","sdk")).lower()
    if mode == "sdk":
        # Interpret input as pool pubkey
        return parse_clmm_account_via_sdk(pool_pubkey_or_b64)
    else:
        # Interpret input as base64 account data
        return parse_clmm_account_raw(pool_pubkey_or_b64)
