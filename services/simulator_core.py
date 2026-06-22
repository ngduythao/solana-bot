
# Lightweight simulator for CLMM (Orca/Raydium-like) and DLMM (Meteora-like)
# Focus: tick math / bins, fee dynamic per leg, partial fill until budget exhausted.

from math import sqrt

def clmm_swap(amount_in, sqrt_price, liquidity, tick_spacing, ticks, fee_bps=30, by_amount_in=True):
    '''
    amount_in: token in (base units)
    sqrt_price: current sqrt(P) (Q64.64-like, but here float)
    liquidity: active L at current tick
    ticks: list of dicts [{sqrt_price_next, liquidity_net}] in price-walk order
    fee_bps: fee in basis points
    Returns: (amount_out, amount_in_consumed, price_end, crossed_ticks)
    '''
    if amount_in <= 0 or liquidity <= 0:
        return 0.0, 0.0, sqrt_price, 0
    amt_in_rem = float(amount_in)
    amt_out_total = 0.0
    crossed = 0
    s = float(sqrt_price)
    L = float(liquidity)
    fee = fee_bps/1e4

    for t in ticks:
        s_next = float(t["sqrt_price_next"])
        # amount in required to move price from s to s_next (x -> y convention)
        # Δx = L*(s_next - s)/(s*s_next)
        if s_next <= 0 or s <= 0: break
        dx_needed = L * (s_next - s) / (s * s_next)
        dx_with_fee = dx_needed / (1 - fee)
        if dx_with_fee <= amt_in_rem + 1e-12:
            # fully consume this range
            amt_in_rem -= dx_with_fee
            # Δy = L*(s - s_next)
            dy = L * (s - s_next)
            amt_out_total += dy
            s = s_next
            L += float(t.get("liquidity_net", 0.0))
            crossed += 1
            if L <= 0: break
        else:
            # partial within current range
            dx_eff = amt_in_rem * (1 - fee)
            # new sqrt price s' solving dx_eff = L*(s' - s)/(s*s')
            # rearrange: dx_eff * s*s' = L*(s' - s)
            # This implies solving for s'; we can approximate with small step:
            # s' = s + dx_eff * s*s' / L  ≈ s + dx_eff * s*s / L   (assuming s' ~ s for small step)
            s_prime = s + dx_eff * s * s / L
            if s_prime >= s_next: s_prime = s_next - 1e-12
            dy = L * (s - s_prime)
            amt_out_total += dy
            amt_in_rem = 0.0
            s = s_prime
            break

    return float(amt_out_total), float(amount_in - amt_in_rem), float(s), crossed

def dlmm_swap(amount_in, bins, fee_bps=30):
    '''
    Meteora-like DLMM bins: list of {price, liquidity, fee_bps?} from best to worse.
    Greedy fill across bins; supports per-bin dynamic fee if present.
    Returns (amount_out, amount_in_consumed, bins_used)
    '''
    if amount_in <= 0: return 0.0, 0.0, 0
    rem = float(amount_in); out=0.0; used=0
    for b in bins:
        if rem <= 1e-12: break
        price = float(b["price"]); L = float(b["liquidity"])
        fee = (b.get("fee_bps", fee_bps))/1e4
        # max fill by liquidity: assume linear around bin price (simplified)
        max_in_bin = L * price  # rough budget: swap against this bin up to its liquidity * price
        take = min(rem, max_in_bin)
        out += take * (1 - fee) / price
        rem -= take
        used += 1
    return float(out), float(amount_in - rem), used
