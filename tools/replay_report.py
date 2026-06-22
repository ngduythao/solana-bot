
# Quick offline report from analytics.csv
import pandas as pd, sys, os

def main(csv_path):
    if not os.path.exists(csv_path):
        print("CSV not found:", csv_path); return 1
    df = pd.read_csv(csv_path)
    if df.empty: 
        print("Empty CSV"); return 0
    cols = df.columns.tolist()
    print("Columns:", cols)
    if 'ts' in df.columns:
        df['ts'] = pd.to_datetime(df['ts'])
    pnl = df['pnl_usd'] if 'pnl_usd' in df.columns else None
    if pnl is not None:
        print("Total PnL USD:", float(pnl.sum()))
        if 'pair' in df.columns:
            print("\nPnL by pair:")
            print(pnl.groupby(df['pair']).sum())
    if 'ev_bps' in df.columns:
        print("\nEV mean (bps):", float(df['ev_bps'].mean()))
    if 'ev_bps' in df.columns and pnl is not None:
        print("\nHit-rate:", float((pnl>=0).mean())*100, "%")
    return 0

if __name__=="__main__":
    csv = sys.argv[1] if len(sys.argv)>1 else "analytics.csv"
    raise SystemExit(main(csv))
