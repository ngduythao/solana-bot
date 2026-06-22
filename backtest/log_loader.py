
import json, pandas as pd
from typing import List, Dict, Any

def load_audit_jsonl(path: str) -> pd.DataFrame:
    rows=[]
    with open(path,'r') as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try:
                obj=json.loads(line)
                rows.append(obj)
            except Exception:
                continue
    if not rows:
        return pd.DataFrame()
    df=pd.DataFrame(rows)
    # expected keys: ts, route, ev_bps, pnl_usd, fees_usd, fill, reason, venue, pair, symbol
    for k in ["ts","route","ev_bps","pnl_usd","fees_usd","fill"]:
        if k not in df.columns:
            df[k]=None
    return df

def summarize(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty: 
        return {"trades":0}
    d = {}
    df=df.copy()
    df['pnl_usd']=pd.to_numeric(df['pnl_usd'], errors='coerce').fillna(0.0)
    df['ev_bps']=pd.to_numeric(df['ev_bps'], errors='coerce').fillna(0.0)
    d['trades']=int((df['pnl_usd']!=0).sum())
    d['gross_pnl_usd']=round(df['pnl_usd'].sum(),2)
    d['avg_ev_bps']=round(df['ev_bps'].mean(),2)
    d['p50_ev_bps']=round(df['ev_bps'].median(),2)
    return d
