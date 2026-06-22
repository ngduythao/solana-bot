
import os, json, glob

IDL_DIR = os.path.join(os.path.dirname(__file__), "idl")

def load_idl_by_name(name: str):
    name = (name or "").lower()
    for p in glob.glob(os.path.join(IDL_DIR, "*.json")):
        fn = os.path.basename(p).lower()
        if name and name in fn:
            try:
                return json.load(open(p,"r"))
            except Exception:
                continue
    return {}
