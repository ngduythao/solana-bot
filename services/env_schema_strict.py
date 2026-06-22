
import os, sys, json
REQUIRED = ["REDIS_URL","RPC_PRIMARY"]
RECOMMENDED = ["JITO_RELAYS","TIP_STREAM_URL","TIP_FLOOR_URL"]
def main():
    miss=[k for k in REQUIRED if not os.getenv(k)]
    if miss:
        print(json.dumps({"ok":False,"missing":miss})); sys.exit(1)
    print(json.dumps({"ok":True,"recommended":[k for k in RECOMMENDED if not os.getenv(k)]}))
if __name__=="__main__": main()
