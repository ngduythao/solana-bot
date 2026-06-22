use serde_json::Value;

pub struct ExecLimits {
    pub max_cu_per_tx: u64,
    pub max_hops: usize,
    pub price_limit_bps: u64,
}

pub fn load_limits(cfg: &Value) -> ExecLimits {
    let limits = &cfg["limits"];
    ExecLimits {
        max_cu_per_tx: limits
            .get("max_cu_per_tx")
            .and_then(|v| v.as_u64())
            .unwrap_or(700_000),
        max_hops: limits.get("max_hops").and_then(|v| v.as_u64()).unwrap_or(3) as usize,
        price_limit_bps: limits
            .get("price_limit_bps")
            .and_then(|v| v.as_u64())
            .unwrap_or(35),
    }
}

pub fn guard_route(norm: &Value, limits: &ExecLimits) -> bool {
    let est_cu = norm.get("est_cu").and_then(|v| v.as_u64()).unwrap_or(0);
    if est_cu > limits.max_cu_per_tx {
        return false;
    }
    let legs = norm
        .get("legs")
        .and_then(|v| v.as_array())
        .map(|a| a.len())
        .unwrap_or(0);
    if legs > limits.max_hops {
        return false;
    }
    true
}

pub fn enforce_min_out_per_leg(_ixs: &mut Vec<Vec<u8>>, _norm: &Value, _limits: &ExecLimits) {
    // TODO: Implement per-leg min_out guard at instruction level.
}
