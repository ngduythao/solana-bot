
import os, yaml, json, sys
from pathlib import Path

def validate_yaml(data, schema):
    # minimal structural check to avoid adding jsonschema dependency
    if not isinstance(data, dict): return False, "root not object"
    if "program_id" not in data or "metas" not in data: return False, "missing keys"
    if not isinstance(data["metas"], dict): return False, "metas not object"
    return True, "ok"

def main():
    base = Path(__file__).parent
    for fname in ["programs.yaml", "market_registry.yaml"]:
        p = base / fname
        if not p.exists(): 
            print(f"[metas_validator] skip missing {fname}")
            continue
        d = yaml.safe_load(open(p)) or {}
        if fname=="programs.yaml":
            for k in ("phoenix","openbook"):
                ok, msg = validate_yaml(d.get(k,{}), {})
                print(f"[{fname}:{k}] {msg}")
        else:
            print(f"[{fname}] loaded keys: {list(d.keys())}")
    print("[metas_validator] done")

if __name__ == "__main__":
    main()
