// Read Raydium CLMM pool state via @raydium-io/raydium-sdk-v2 (no manual offsets)
(async () => {
  try {
    const poolAddr = process.argv[2]; if(!poolAddr){ console.error("Usage: node read_raydium_clmm.js <poolPubkey>"); process.exit(1); }
    let web3, sdk;
    try {
      web3 = await import('@solana/web3.js');
      sdk = await import('@raydium-io/raydium-sdk-v2');
    } catch (e) {
      const { execSync } = await import('node:child_process');
      execSync('npm init -y >/dev/null 2>&1 || true');
      execSync('npm install @solana/web3.js @raydium-io/raydium-sdk-v2 >/dev/null 2>&1');
      web3 = await import('@solana/web3.js');
      sdk = await import('@raydium-io/raydium-sdk-v2');
    }
    const { Connection, PublicKey } = web3;
    const endpoint = process.env.RPC_PRIMARY || process.env.RPC || 'https://api.mainnet-beta.solana.com';
    const conn = new Connection(endpoint, 'processed');
    // minimal init
    const poolPubkey = new PublicKey(poolAddr);
    // SDK v2 exposes helpers under Raydium.load...; fallback to direct account read if needed.
    // Here we try to fetch from API then fall back
    try {
      const { Raydium, ApiPoolInfo } = sdk;
      const api = await Raydium.loadApi({ connection: conn });
      const pools = await api.getClmmPools({ ids: [poolPubkey.toBase58()] });
      const p = pools[0];
      if (p) {
        console.log(JSON.stringify({
          ok:true, type:"raydium_clmm",
          sqrtPriceX64: p.sqrtPriceX64?.toString?.() || "0",
          liquidity: p.liquidity?.toString?.() || "0",
          fee_bps: p.feeRate || 0,
          tickSpacing: p.tickSpacing || 0,
          tickCurrentIndex: p.tickCurrent || 0
        }));
        return;
      }
    } catch (_) {}
    // Fallback: raw account (without offsets we return minimal)
    const acc = await conn.getAccountInfo(poolPubkey);
    console.log(JSON.stringify({ok:true,type:"raydium_clmm", raw: acc?.data?.length || 0}));
  } catch (e) {
    console.error("ERR", e?.message || e);
    process.exit(2);
  }
})();
