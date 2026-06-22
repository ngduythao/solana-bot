
// Enforce per-leg min_out by adjusting instruction data (placeholder).
// Integrate with the DEX program-specific IX formats to set amountOutMinimum/limit.
pub fn enforce_min_out_bytes(ix: &mut Vec<u8>, _min_out: u64) {
    // TODO: parse & patch instruction for each DEX; left as scaffold.
}
