
#!/usr/bin/env python3
import os, json, pickle, argparse
from pathlib import Path

try:
    from sklearn.ensemble import GradientBoostingClassifier
except Exception:
    GradientBoostingClassifier = None

def load_data(path):
    X=[]; y=[]
    with open(path) as f:
        for line in f:
            try:
                j=json.loads(line).get("reconcile",{})
                # crude label: 1 if delta>0 else 0
                y.append(1 if int(j.get("delta",0))>0 else 0)
                # crude features from reconcile
                X.append([
                    float(j.get("fee_bps",30)),
                    float(j.get("size_q0",0))/1e6,
                    float(j.get("lat_p50",0)),
                    float(j.get("lat_p95",0)),
                    float(j.get("hour",0))
                ])
            except Exception:
                pass
    return X,y

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="path to export NDJSON")
    ap.add_argument("--out", default="/etc/solbot/ev_model.pkl")
    args=ap.parse_args()

    X,y = load_data(args.data)
    if not X or GradientBoostingClassifier is None:
        print("Insufficient data or sklearn missing — skipping model")
        return 0

    mdl = GradientBoostingClassifier()
    mdl.fit(X,y)
    Path(os.path.dirname(args.out)).mkdir(parents=True, exist_ok=True)
    with open(args.out,"wb") as f:
        pickle.dump(mdl,f)
    print("Saved model to", args.out)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
