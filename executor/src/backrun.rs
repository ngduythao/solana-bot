use serde::Deserialize;
use tokio::sync::mpsc;
use tracing::info;

#[derive(Debug, Deserialize, Clone)]
pub struct BackrunCfg {
    pub min_swap_usd: u64,
    pub cooldown_ms: u64,
}

pub async fn run_backrun(_cfg: BackrunCfg, _tx_sender: mpsc::Sender<String>) {
    info!("Python backrun service handles WS in this version");
}
