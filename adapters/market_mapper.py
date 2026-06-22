
#!/usr/bin/env python3
"""Market Mapper CLI
Usage:
  python adapters/market_mapper.py --phoenix --market SOL_USDC --program <PROGRAM_ID> --owner <OWNER_PUBKEY> --meta bids:rw,asks:rw,eventQueue:w,baseVault:rw,quoteVault:rw
  python adapters/market_mapper.py --openbook --market SOL_USDC --program <PROGRAM_ID> --owner <OWNER_PUBKEY> --meta bids:rw,asks:rw,eventQueue:w,baseVault:rw,quoteVault:rw
  python adapters/market_mapper.py --from-idl path/to/idl.json --program <PROGRAM_ID> --dex phoenix|openbook --market SOL_USDC --owner <OWNER_PUBKEY>
Writes to adapters/programs.yaml and adapters/market_registry.yaml
"""
import os, sys, json, yaml, argparse
from pathlib import Path

BASE = Path(__file__).parent
PROG = BASE/'programs.yaml'
REG  = BASE/'market_registry.yaml'

def load_yaml(p): return yaml.safe_load(open(p)) if p.exists() else {}
def dump_yaml(p, obj): yaml.safe_dump(obj, open(p,'w'), sort_keys=False)

def parse_metas(meta_str):
    metas={}
    for part in (meta_str or "").split(","):
        if not part: continue
        k, mode = part.split(":",1)
        metas[k.strip()]={"writable":"w" in mode, "signer":"s" in mode}
    return metas

def ensure_path(d, keys):
    for k in keys: d.setdefault(k, {})
    return d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phoenix", action="store_true")
    ap.add_argument("--openbook", action="store_true")
    ap.add_argument("--from-idl", type=str, default="")
    ap.add_argument("--program", type=str, required=False)
    ap.add_argument("--market", type=str, required=True)
    ap.add_argument("--owner", type=str, required=True)
    ap.add_argument("--meta", type=str, default="")
    args = ap.parse_args()

    dex = "phoenix" if args.phoenix else ("openbook" if args.openbook else None)
    if not dex and not args.from_idl:
        print("Specify --phoenix or --openbook or --from-idl"); sys.exit(1)
    if not args.program and not args.from_idl:
        print("--program required when not using --from-idl"); sys.exit(1)

    programs = load_yaml(PROG) or {}
    registry = load_yaml(REG) or {}

    if args.from_idl:
        # Minimal parse: load IDL and suggest common account names
        idl = json.load(open(args.from_idl))
        accs = [a.get("name") for a in idl.get("accounts",[]) if isinstance(a, dict)]
        # default mapping guess
        metas = {}
        for name in accs:
            nm = str(name).lower()
            meta = {"writable": False, "signer": False}
            if "vault" in nm or "bids" in nm or "asks" in nm or "queue" in nm:
                meta["writable"]=True
            if "owner" == nm or "authority" in nm:
                meta["signer"]=True
            metas[name]=meta
        if not dex:
            print("--dex phoenix|openbook required with --from-idl"); sys.exit(1)
        pid = args.program or idl.get("metadata",{}).get("address","")
    else:
        metas = parse_metas(args.meta)
        pid = args.program
        if not metas:
            print("Provide --meta list (e.g., bids:rw,asks:rw,eventQueue:w,baseVault:rw,quoteVault:rw)"); sys.exit(1)

    programs = ensure_path(programs, [dex])
    programs[dex]["program_id"] = pid or programs[dex].get("program_id","")
    programs[dex]["metas"] = metas or programs[dex].get("metas",{})

    registry = ensure_path(registry, [dex])
    m = registry[dex] or {}
    m[args.market] = {"market": f"<{dex.upper()}_{args.market}_MARKET_PUBKEY>", "owner_placeholder": args.owner, "metas": metas}
    registry[dex] = m

    dump_yaml(PROG, programs)
    dump_yaml(REG, registry)
    print("Updated: programs.yaml and market_registry.yaml")

if __name__ == "__main__":
    main()
