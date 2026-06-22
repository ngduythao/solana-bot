
use anyhow::Result;
pub struct SubmitResp { pub accepted: bool }
pub async fn submit_bundle(_txs: Vec<Vec<u8>>, _endpoint: &str) -> Result<SubmitResp> {
    // TODO: implement tonic client with real proto
    Ok(SubmitResp{accepted: true})
}
