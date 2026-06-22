
# Backtest Suite

## Inputs
- **CEX CSV**: `ts,symbol,price`
- **DEX CSV**: `ts,pair,price,fee_bps`
  - `ts` in milliseconds since epoch or ISO8601; the runner will parse both.
  - `price` as quote in USDC/USDT terms.

## Run
```bash
python backtest/runner.py   --cex data/cex_prices.csv   --dex data/dex_quotes.csv   --routes SOLUSDT:SOL/USDC,JUPUSDT:JUP/USDC,WIFUSDT:WIF/USDC,BONKUSDT:BONK/USDC   --slippage_bps 15   --ev_threshold_bps 3   --latency_ms 80   --out report.csv
```

## Output
- `report.csv` with per-trade records.
- Summary printed: trades, hit-rate (sim→fill), gross/net PnL, fee burn estimate, average EV, etc.
