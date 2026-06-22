import pandas as pd, matplotlib.pyplot as plt, argparse, pathlib
def main(path):
    p = pathlib.Path(path)
    if not p.exists():
        print("CSV not found:", path); return
    df = pd.read_csv(p)
    if df.empty:
        print("CSV empty"); return
    df['ts'] = pd.to_datetime(df['ts'])
    hourly = df.set_index('ts').resample('1H').agg({'pnl_usd':'sum', 'size_usd':'sum'}).fillna(0)
    hourly.to_csv(p.with_suffix('.hourly.csv'))
    plt.figure()
    hourly['pnl_usd'].cumsum().plot(title='Cumulative PnL (real, Pyth)')
    out = p.with_suffix('.png')
    plt.savefig(out, bbox_inches='tight'); print("Saved:", out, p.with_suffix('.hourly.csv'))
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument('--csv', default='/app/analytics.csv'); args = ap.parse_args(); main(args.csv)
