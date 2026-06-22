use anyhow::*;
use solana_client::rpc_client::RpcClient;
use solana_sdk::{
    compute_budget::ComputeBudgetInstruction,
    instruction::Instruction,
    message::Message,
    pubkey::Pubkey,
    signature::{read_keypair_file, Keypair},
    transaction::Transaction,
};
use std::sync::Arc;

pub struct SolanaExec {
    pub rpc: Arc<RpcClient>,
    pub kp: Keypair,
}

impl SolanaExec {
    pub fn new(rpc_url: &str, keypair_path: &str) -> Result<Self> {
        let kp = read_keypair_file(keypair_path).map_err(|err| anyhow!(err.to_string()))?;
        let rpc = Arc::new(RpcClient::new(rpc_url.to_string()));
        Ok(Self { rpc, kp })
    }
    pub fn build_with_budget(
        &self,
        payer: &Pubkey,
        ix: Vec<Instruction>,
        micro_lamports: u64,
    ) -> Result<Transaction> {
        let mut ixs = vec![
            ComputeBudgetInstruction::set_compute_unit_price(micro_lamports),
            ComputeBudgetInstruction::set_compute_unit_limit(1_200_000),
        ];
        ixs.extend(ix);
        let recent = self.rpc.get_latest_blockhash()?;
        let msg = Message::new(&ixs, Some(payer));
        let tx = Transaction::new(&[&self.kp], msg, recent);
        Ok(tx)
    }
}

// === B-pack additions ===
// - Read 'norm' field from opportunity: per-leg min_out, est_cu
// - Enforce max CU per tx from config
// - If JITO_BUNDLES=1 and JITO_ENDPOINT set, attempt to wrap tx in bundle (stub)
// - Send webhook alerts on drift, RPC errors, or circuit-breaker trips
