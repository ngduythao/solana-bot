
import os, stat, pathlib

def load_system_env():
    path = pathlib.Path('/etc/solbot/.env')
    if path.exists():
        for line in path.read_text().splitlines():
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line: continue
            k,v = line.split('=',1)
            os.environ.setdefault(k.strip(), v.strip())

def check_keypair_perms(file_path: str) -> bool:
    if not file_path or not os.path.exists(file_path): return False
    st = os.stat(file_path)
    # owner read/write only recommended (0o600)
    bad = (st.st_mode & 0o077) != 0
    return not bad
