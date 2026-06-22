
from cryptography.fernet import Fernet, InvalidToken
import os, sys, json, yaml

KEY_ENV="STRATEGY_FERNET_KEY"
ENC_PATH="strategy/strategy.enc"
PLAIN_PATH="strategy/strategy.yaml"

def load_strategy():
    key=os.getenv(KEY_ENV,"")
    if key and os.path.exists(ENC_PATH):
        f=Fernet(key.encode())
        data=open(ENC_PATH,"rb").read()
        try:
            dec=f.decrypt(data)
            return yaml.safe_load(dec)
        except InvalidToken:
            raise SystemExit("Invalid STRATEGY_FERNET_KEY for strategy.enc")
    # fallback plain yaml
    return yaml.safe_load(open(PLAIN_PATH, "r")) if os.path.exists(PLAIN_PATH) else {}

if __name__=="__main__":
    print(load_strategy())
