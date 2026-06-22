
import shutil, os, sys
mode = sys.argv[1] if len(sys.argv)>1 else "freeze"
if mode=="freeze":
    shutil.copyfile("config/pools.yaml","config/pools.lock.yaml")
    print("frozen -> config/pools.lock.yaml")
elif mode=="unfreeze":
    if os.path.exists("config/pools.lock.yaml"):
        os.remove("config/pools.lock.yaml"); print("unfrozen")
    else:
        print("already unfrozen")
else:
    print("usage: python tools/pools_freeze.py [freeze|unfreeze]")
