
# Audit Log Schema (CSV)
Columns:
- ts: unix seconds
- pair
- route_legs: json string list of legs (amm,pool,input,output,qty_in,min_out)
- ev_bps
- priority_fee_usd
- rpc_fee_usd
- pnl_usd
- cu_used
- decision: taken|skipped
- reason: optional text
