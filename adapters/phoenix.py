
# Phoenix maker adapter: build signed transaction message (no RPC send)
import os, time, base58
from typing import Optional
try:
    from solana.transaction import Transaction
    from solana.rpc.types import TxOpts
    from solders.keypair import Keypair
    LIBS_OK = True
except Exception:
    LIBS_OK = False

def build_signed_order_tx(recent_blockhash: str, instructions: list, keypair_path: str) -> Optional[str]:
    if not LIBS_OK:
        return None
    kp = Keypair.from_json(open(keypair_path).read())
    tx = Transaction()
    for ix in instructions:
        tx.add(ix)
    tx.recent_blockhash = recent_blockhash
    tx.sign(kp)  # sign locally
    # return base64 wire-format (executor will bundle via Jito)
    return base58.b58encode(tx.serialize()).decode()
