
import os, sys

required = ["HELIUS_RPC"]
missing = [k for k in required if not os.getenv(k)]
if missing:
    print("Missing env:", ", ".join(missing))
    sys.exit(1)

mode = (os.getenv("JITO_MODE","rest") or "rest").lower()
if mode == "grpc":
    if not os.getenv("JITO_ENDPOINT"):
        print("JITO_MODE=grpc but JITO_ENDPOINT is empty")
        sys.exit(2)
print("env ok")
