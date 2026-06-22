
import os, json, subprocess, yaml, sys

SDK_DIR = os.path.join(os.path.dirname(__file__),'..','sdk')

def run_node(script, args):
    cmd = ["node", os.path.join(SDK_DIR, script)] + args
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode!=0:
        print(p.stderr.strip())
        return None
    try:
        return json.loads(p.stdout.strip())
    except Exception:
        print("Invalid JSON from", script)
        return None

def update_pools_yaml(mintA, mintB, cluster="mainnet-beta"):
    path = "config/pools.yaml"
    cfg = yaml.safe_load(open(path))
    orca = run_node("derive_orca.js", [cluster, mintA, mintB]) or {}
    ray  = run_node("derive_raydium.js", [cluster, mintA, mintB]) or {}
    met  = run_node("derive_meteora.js", [cluster, mintA, mintB]) or {}

    pools = cfg.get("pools", [])
    def add_pool(name, ptype, addr, tick_arrays=None):
        pools.append({"name": name, "type": ptype, "pool_account": addr, "tick_arrays": tick_arrays or []})
    for x in orca.get("pools", []):
        add_pool(f"{mintA}/{mintB} - Orca", "orca_whirlpool", x["address"], orca.get("tickArrays",[]))
    for x in ray.get("pools", []):
        add_pool(f"{mintA}/{mintB} - Raydium", "raydium_clmm", x["address"])
    for x in met.get("pools", []):
        add_pool(f"{mintA}/{mintB} - Meteora", "meteora_dlmm", x["address"])

    cfg["pools"] = pools
    yaml.safe_dump(cfg, open(path,"w"))
    print("Updated pools.yaml")

if __name__=="__main__":
    if len(sys.argv)<3:
        print("Usage: python tools/discovery.py <mintA> <mintB> [cluster]")
        sys.exit(1)
    mintA, mintB = sys.argv[1], sys.argv[2]
    cluster = sys.argv[3] if len(sys.argv)>3 else "mainnet-beta"
    update_pools_yaml(mintA, mintB, cluster)
