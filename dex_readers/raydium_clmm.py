
import os, base64, asyncio, httpx, json

RPC = os.getenv("ONCHAIN_RPC","http://rpc_router:8899")

async def rpc_get_account(addr: str):
    payload={"jsonrpc":"2.0","id":1,"method":"getAccountInfo","params":[addr,{"encoding":"base64"}]}
    async with httpx.AsyncClient(timeout=1.5) as c:
        r = await c.post(RPC, json=payload)
        r.raise_for_status()
        return r.json()

async def rpc_get_program_accounts(prog: str, filters=None):
    params=[prog, { "encoding":"base64" }]
    if filters: params[1]["filters"]=filters
    payload={"jsonrpc":"2.0","id":1,"method":"getProgramAccounts","params":params}
    async with httpx.AsyncClient(timeout=2.5) as c:
        r = await c.post(RPC, json=payload)
        r.raise_for_status()
        return r.json()

# Raydium CLMM reader (stub). In production: parse tick arrays & pool state.
class RaydiumCLMMReader:
    def __init__(self, rpc_base: str):
        self.rpc_base = rpc_base

    async def read_pool(self, pool_addr: str):
        return {
            "type": "CLMM",
            "pool": pool_addr,
            "tick_spacing": 60,
            "current_tick": 0,
            "liquidity": 0,
            "fee_tier_bps": 25,
        }


def parse_account_layout(data_b64: str):
    # TODO: implement real Raydium CLMM layout parsing
    # For now, return minimal placeholders to not break simulator
    return {"price": 1.0, "liquidity": 1_000_000, "fee_tier_bps": 30, "bins": []}
