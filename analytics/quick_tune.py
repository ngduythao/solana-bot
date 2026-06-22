import argparse, yaml, pandas as pd, numpy as np, pathlib, sys

def suggest(cfg, df):
    tips = []
    # Hit-rate & PnL per fill
    hr = (df["pnl_usd"]>0).mean() if len(df)>0 else 0
    avg_ev = df["ev_bps"].mean() if len(df)>0 else 0
    # Congestion proxy from micro_fee
    med_micro = df["micro_fee"].median() if "micro_fee" in df.columns else 10
    # 1) EV threshold
    if hr < 0.55 and avg_ev < cfg["ev"]["fire_threshold_bps"]+0.5:
        cfg["ev"]["fire_threshold_bps"] = min(cfg["ev"]["fire_threshold_bps"]+0.5, 6.0)
        tips.append("Tăng ev.fire_threshold_bps +0.5 do hit-rate thấp")
    elif hr > 0.70:
        cfg["ev"]["fire_threshold_bps"] = max(cfg["ev"]["fire_threshold_bps"]-0.3, 2.0)
        tips.append("Giảm ev.fire_threshold_bps -0.3 do hit-rate cao")

    # 2) Priority fee cap
    if (df["pnl_usd"] < 0).sum() > 0 and med_micro > 50:
        cfg["fees"]["priority_fee_budget_pct_of_ev"] = max(0.12, cfg["fees"]["priority_fee_budget_pct_of_ev"]-0.02)
        tips.append("Giảm fees.priority_fee_budget_pct_of_ev -0.02 do phí cao")

    # 3) Slippage cap
    if (df["ev_bps"] - df["pnl_usd"].abs()*10000/np.maximum(df["size_usd"],1)).mean() < 0:
        cfg["risk"]["slippage_cap_bps"] = max(15, cfg["risk"]["slippage_cap_bps"]-2)
        tips.append("Giảm risk.slippage_cap_bps -2 do slip thực cao")

    # 4) Inventory
    if df["exp_pct"].max() > cfg["ai"]["inventory"]["max_base_pct_nav"]*0.9:
        cfg["ai"]["inventory"]["hedge_strength"] = min(1.5, cfg["ai"]["inventory"]["hedge_strength"]+0.2)
        tips.append("Tăng hedge_strength +0.2 để giảm lệch tồn kho")

    # 5) Scheduler
    if hr < 0.5:
        bh = set(cfg["ai"]["scheduler"].get("boost_hours_utc", []))
        for h in [0,1,13,14,15,16,20]:
            bh.add(h)
        cfg["ai"]["scheduler"]["boost_hours_utc"] = sorted(bh)
        tips.append("Mở rộng boost_hours_utc do hiệu suất thấp")
    return cfg, tips

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="/app/analytics.csv")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--write", action="store_true", help="Ghi đè config.yaml")
    args = ap.parse_args()

    p = pathlib.Path(args.csv)
    if not p.exists():
        print("Không thấy CSV:", p); sys.exit(1)
    df = pd.read_csv(p)
    if df.empty:
        print("CSV trống"); sys.exit(1)

    cfg = yaml.safe_load(open(args.config))
    new_cfg, tips = suggest(cfg, df)

    print("=== ĐỀ XUẤT TỰ ĐỘNG ===")
    for t in tips: print("-", t)
    if args.write:
        with open(args.config, "w") as f: yaml.safe_dump(new_cfg, f, sort_keys=False)
        print("Đã ghi cấu hình tối ưu vào", args.config)
    else:
        print("(Chạy lại với --write để ghi cấu hình)")

if __name__ == "__main__":
    main()
