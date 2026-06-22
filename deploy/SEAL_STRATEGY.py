
#!/usr/bin/env python3
import os, yaml
from cryptography.fernet import Fernet
KEY_ENV="STRATEGY_FERNET_KEY"
key=os.getenv(KEY_ENV)
if not key:
    key=Fernet.generate_key().decode()
    print("Generated key:", key)
f=Fernet(key.encode())
data=open("strategy/strategy.yaml","rb").read()
enc=f.encrypt(data)
open("strategy/strategy.enc","wb").write(enc)
print("Encrypted -> strategy/strategy.enc (keep key safe in /etc/solbot/.env as STRATEGY_FERNET_KEY)")
