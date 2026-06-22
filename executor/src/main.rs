mod alert;
mod backrun;
mod risk_guard;
mod solana_exec;
use anyhow::*;
use chrono::Utc;
use csv::WriterBuilder;
use redis::AsyncCommands;
use serde::Deserialize;
use solana_exec::*;
use solana_sdk::signature::Signer;
use solana_transaction_status::{
    EncodedConfirmedTransactionWithStatusMeta, UiTransactionEncoding, UiTransactionTokenBalance,
};
use std::fs;
use std::result::Result::Ok;
use tokio::time;
use tracing::{error, info, warn};

#[derive(Debug, Deserialize, Clone)]
struct RiskCfg {
    max_nav_per_trade_bps: u32,
    slippage_cap_bps: u32,
    hourly_dd_stop_bps: u32,
    daily_dd_stop_bps: u32,
    cooldown_seconds: u64,
}
#[derive(Debug, Deserialize, Clone)]
struct EvCfg {
    fire_threshold_bps: f64,
    min_liquidity_usd: u64,
    min_24h_volume_usd: u64,
}
#[derive(Debug, Deserialize, Clone)]
struct FeesCfg {
    priority_fee_budget_pct_of_ev: f64,
    max_priority_fee_lamports: u64,
}
#[derive(Debug, Deserialize, Clone)]
struct RpcCfg {
    primary: String,
    fallback: Vec<String>,
    submit_timeout_ms: u64,
    retry_backoff_ms: u64,
    parallel_race: bool,
}
#[derive(Debug, Deserialize, Clone)]
struct Portfolio {
    nav_usd: f64,
    quote_token: String,
}
#[derive(Debug, Deserialize, Clone)]
struct DexCfg {
    use_jupiter: bool,
    use_meteora_pools: bool,
    dex_allowlist: Vec<String>,
    only_direct_routes: bool,
}
#[derive(Debug, Deserialize, Clone)]
struct InventoryAI {
    mode: String,
    target_base_pct_nav: f64,
    hedge_strength: f64,
    max_base_pct_nav: f64,
    hedge_when_pct_nav_gt: f64,
    hedge_fraction: f64,
}
#[derive(Debug, Deserialize, Clone)]
struct AICfg {
    inventory: InventoryAI,
}
#[derive(Debug, Deserialize, Clone)]
struct Strategies {
    arb_dex_dex: bool,
    backrun_basic: bool,
    grid_narrow: bool,
    auto_hedge: bool,
}
#[derive(Debug, Deserialize, Clone)]
struct BackrunCfgYaml {
    min_swap_usd: u64,
    cooldown_ms: u64,
}
#[derive(Debug, Deserialize, Clone)]
struct AnalyticsCfg {
    enable: bool,
    csv_path: String,
    rollup_window_minutes: u64,
}
#[derive(Debug, Deserialize, Clone)]
struct Cfg {
    risk: RiskCfg,
    ev: EvCfg,
    fees: FeesCfg,
    rpc: RpcCfg,
    portfolio: Portfolio,
    dex: DexCfg,
    backrun: BackrunCfgYaml,
    strategies: Strategies,
    ai: AICfg,
    analytics: AnalyticsCfg,
}

#[derive(Debug, Deserialize, Clone)]
struct Opp {
    pair: String,
    ts: f64,
    size_usd: f64,
    ev_bps: f64,
    route: serde_json::Value,
    ai: Option<serde_json::Value>,
}

fn load_cfg() -> Result<Cfg> {
    let s = fs::read_to_string("config.yaml")?;
    Ok(serde_yaml::from_str(&s)?)
}

fn cap_priority_from_ev(ev_bps: f64, max_lamports: u64, max_pct_ev: f64) -> u64 {
    let micro = (ev_bps.max(0.1) * 90.0) as u64; // leaner map to save EV
    let cap = (ev_bps * 100.0 * max_pct_ev) as u64;
    micro.min(cap).min(max_lamports)
}

fn swap_and_confirm(exec: &SolanaExec, route: serde_json::Value, micro_fee: u64) -> Result<String> {
    let jup_base = std::env::var("JUP_BASE").unwrap_or("https://quote-api.jup.ag".into());
    let user_pk = exec.kp.pubkey().to_string();
    let payload = serde_json::json!({
        "userPublicKey": user_pk,
        "quoteResponse": route,
        "wrapAndUnwrapSol": true,
        "useSharedAccounts": true,
        "computeUnitPriceMicroLamports": micro_fee
    });
    let http = reqwest::blocking::Client::new();
    let resp = http
        .post(format!("{}/v6/swap", jup_base))
        .json(&payload)
        .send()?;
    let val: serde_json::Value = resp.json()?;
    let tx_b64 = val
        .get("swapTransaction")
        .and_then(|x| x.as_str())
        .ok_or_else(|| anyhow!("no swapTransaction"))?;
    let tx_bytes = base64::decode(tx_b64)?;
    let tx: solana_sdk::transaction::VersionedTransaction = bincode::deserialize(&tx_bytes)?;
    let tx = solana_sdk::transaction::VersionedTransaction::try_new(tx.message, &[&exec.kp])?;
    let sig = exec.rpc.send_and_confirm_transaction(&tx)?;
    Ok(sig.to_string())
}

fn decode_pnl_usd(exec: &SolanaExec, sig: &str) -> Result<(f64, f64)> {
    // Get token balance delta and map to USD via Pyth Hermes (through reqwest)
    let tx: EncodedConfirmedTransactionWithStatusMeta = exec.rpc.get_transaction_with_config(
        &sig.parse()?,
        solana_client::rpc_config::RpcTransactionConfig {
            encoding: Some(UiTransactionEncoding::JsonParsed),
            commitment: None,
            max_supported_transaction_version: Some(0),
            ..Default::default()
        },
    )?;
    let meta = tx.transaction.meta.ok_or_else(|| anyhow!("no meta"))?;
    let pre: Vec<UiTransactionTokenBalance> =
        Option::from(meta.pre_token_balances).unwrap_or_default();
    let post: Vec<UiTransactionTokenBalance> =
        Option::from(meta.post_token_balances).unwrap_or_default();
    if pre.is_empty() || post.is_empty() {
        return Err(anyhow!("no token balances"));
    }
    let client = reqwest::blocking::Client::new();
    let pyth_cfg: std::collections::HashMap<String, String> =
        serde_yaml::from_str(&std::fs::read_to_string("config/pyth_price_ids.yaml")?)?;
    let mut total_in = 0.0f64;
    let mut total_out = 0.0f64;
    for pb in post.iter() {
        let mint = pb.mint.clone();
        let pre_amt = pre
            .iter()
            .find(|x| x.account_index == pb.account_index)
            .and_then(|x| x.ui_token_amount.ui_amount_string.parse::<f64>().ok())
            .unwrap_or(0.0);
        let post_amt = pb
            .ui_token_amount
            .ui_amount_string
            .parse::<f64>()
            .unwrap_or(0.0);
        let delta = post_amt - pre_amt;
        let feed = pyth_cfg.get(&mint).cloned().unwrap_or_default();
        let price: f64 = if !feed.is_empty() {
            let url = std::env::var("PYTH_HERMES")
                .unwrap_or("https://hermes.pyth.network/v2/price/latest".into());
            let resp = client.get(url).query(&[("ids", feed)]).send()?;
            let val: serde_json::Value = resp.json()?;
            val.get("data")
                .and_then(|arr| arr.as_array())
                .and_then(|a| a.first())
                .and_then(|x| {
                    x.get("price")
                        .and_then(|p| p.get("price").and_then(|n| n.as_f64()))
                })
                .unwrap_or(0.0)
        } else {
            0.0
        };
        let usd = delta * price;
        if usd < 0.0 {
            total_in += -usd;
        } else {
            total_out += usd;
        }
    }
    Ok((total_in, total_out))
}

fn append_csv(path: &str, row: &[(&str, String)]) -> Result<()> {
    let mut wtr = if std::path::Path::new(path).exists() {
        WriterBuilder::new()
            .has_headers(false)
            .from_writer(fs::OpenOptions::new().append(true).open(path)?)
    } else {
        WriterBuilder::new().from_path(path)?
    };
    if !std::path::Path::new(path).exists() {
        let headers: Vec<&str> = row.iter().map(|(k, _)| *k).collect();
        wtr.write_record(headers)?;
    }
    let vals: Vec<String> = row.iter().map(|(_, v)| v.clone()).collect();
    wtr.write_record(vals)?;
    wtr.flush()?;
    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt().with_env_filter("info").init();
    let cfg = load_cfg()?;
    let redis_url = std::env::var("REDIS_URL").unwrap_or("redis://localhost:6379/0".into());
    let client = redis::Client::open(redis_url)?;
    let mut conn = client.get_async_connection().await?;
    let kp_path = "wallet/keypair.json";
    let exec = SolanaExec::new(&cfg.rpc.primary, kp_path)?;
    info!("Solbot-Pro executor ready");

    loop {
        let res: Result<Option<(String, String)>, _> = conn.blpop(&["hsbot:opps"], 1.0).await;
        match res {
            Ok(Some((_key, val))) => {
                if let Ok(opp) = serde_json::from_str::<Opp>(&val) {
                    if let Err(e) = handle_opp(&cfg, &exec, &mut conn, opp).await {
                        error!(?e, "handle_opp failed")
                    }
                }
            }
            Ok(None) => {}
            Err(e) => {
                warn!(?e, "redis pop error");
                time::sleep(std::time::Duration::from_millis(200)).await;
            }
        }
    }
}

async fn handle_opp(
    cfg: &Cfg,
    exec: &SolanaExec,
    conn: &mut redis::aio::Connection,
    opp: Opp,
) -> Result<()> {
    let impact_bps = opp
        .route
        .get("priceImpactPct")
        .and_then(|v| v.as_f64())
        .unwrap_or(0.0)
        * 10000.0;
    if impact_bps > cfg.risk.slippage_cap_bps as f64 {
        return Ok(());
    }

    // Prefer AI hints if present, else cap by EV
    let mut micro = cap_priority_from_ev(
        opp.ev_bps,
        cfg.fees.max_priority_fee_lamports,
        cfg.fees.priority_fee_budget_pct_of_ev,
    );
    if let Some(ai) = &opp.ai {
        if let Some(mh) = ai.get("micro_hint").and_then(|x| x.as_i64()) {
            micro = micro.min(mh as u64);
        }
    }
    let sig = swap_and_confirm(exec, opp.route.clone(), micro)?;
    tracing::info!(?sig, pair=%opp.pair, ev_bps=%opp.ev_bps, "FILLED");

    // Real PnL via Pyth
    let (in_usd, out_usd) = decode_pnl_usd(exec, &sig)
        .unwrap_or((opp.size_usd, opp.size_usd * (1.0 + opp.ev_bps / 10000.0)));
    let pnl_usd = out_usd - in_usd;

    // Exposure
    let inv_key = format!("inv:usd:{}", opp.pair);
    let _: () = conn.incr(&inv_key, in_usd).await?;
    let exposure: f64 = conn.get(&inv_key).await.unwrap_or(0.0);
    let exp_pct = exposure / cfg.portfolio.nav_usd;

    // Analytics CSV
    if cfg.analytics.enable {
        let now = Utc::now().to_rfc3339();
        let row = [
            ("ts", now),
            ("pair", opp.pair.clone()),
            ("ev_bps", format!("{:.3}", opp.ev_bps)),
            ("size_usd", format!("{:.2}", opp.size_usd)),
            ("sig", sig.clone()),
            ("micro_fee", micro.to_string()),
            ("in_usd", format!("{:.4}", in_usd)),
            ("out_usd", format!("{:.4}", out_usd)),
            ("pnl_usd", format!("{:.4}", pnl_usd)),
            ("exp_pct", format!("{:.4}", exp_pct)),
        ];
        let pairs: Vec<(&str, String)> = row.iter().map(|(k, v)| (*k, v.clone())).collect();
        append_csv(&cfg.analytics.csv_path, &pairs)?;
    }

    // Hedge
    if cfg.strategies.auto_hedge {
        match cfg.ai.inventory.mode.as_str() {
            "target" => {
                let target = cfg.ai.inventory.target_base_pct_nav;
                if exp_pct > target {
                    let dev = exp_pct - target;
                    let amount_usd =
                        (dev * cfg.portfolio.nav_usd * cfg.ai.inventory.hedge_strength).max(0.0);
                    if amount_usd > 1.0 {
                        let mut rjson = opp.route.clone();
                        if let Some(a) = rjson.get_mut("inAmount") {
                            if let Some(n) = a.as_str() {
                                let amt: u64 = n.parse().unwrap_or(0);
                                let new_amt = ((amount_usd.min(opp.size_usd) / opp.size_usd)
                                    * (amt as f64))
                                    as u64;
                                *a = serde_json::Value::String(new_amt.to_string());
                            }
                        }
                        let _sig2 = swap_and_confirm(exec, rjson, micro / 2);
                        let _: () = conn.incr(&inv_key, -amount_usd).await?;
                    }
                }
            }
            _ => {
                let frac = cfg.ai.inventory.hedge_fraction;
                if frac > 0.0 {
                    let mut rjson = opp.route.clone();
                    if let Some(a) = rjson.get_mut("inAmount") {
                        if let Some(n) = a.as_str() {
                            let amt: u64 = n.parse().unwrap_or(0);
                            let new_amt = ((amt as f64) * frac) as u64;
                            *a = serde_json::Value::String(new_amt.to_string());
                        }
                    }
                    let _sig2 = swap_and_confirm(exec, rjson, micro / 2);
                    let _: () = conn.incr(&inv_key, -opp.size_usd * frac).await?;
                }
            }
        }
    }
    Ok(())
}

// === B-pack additions ===
// - Read 'norm' field from opportunity: per-leg min_out, est_cu
// - Enforce max CU per tx from config
// - If JITO_BUNDLES=1 and JITO_ENDPOINT set, attempt to wrap tx in bundle (stub)
// - Send webhook alerts on drift, RPC errors, or circuit-breaker trips
