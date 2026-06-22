
# Safe stub for OpenBook adapters
try:
    from solana.publickey import PublicKey  # noqa
    LIBS_OK=True
except Exception:
    LIBS_OK=False

def build(*args, **kwargs):
    return None
