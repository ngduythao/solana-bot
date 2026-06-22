
import os
def get(name: str, default: str = "") -> str:
    # prefer docker secrets in /run/secrets/<name>, else ENV
    sec_path = f"/run/secrets/{name}"
    if os.path.exists(sec_path):
        try:
            return open(sec_path,'r').read().strip()
        except Exception:
            pass
    return os.getenv(name, default)
