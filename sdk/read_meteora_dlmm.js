// Read Meteora DLMM pool state via @meteora-ag/dlmm (no manual offsets)
(async () => {
  try {
    const poolAddr = process.argv[2]; if(!poolAddr){ console.error("Usage: node read_meteora_dlmm.js <poolPubkey>"); process.exit(1); }
    let web3, dlmm;
    try {
      web3 = await import('@solana/web3.js');
      dlmm = (await import('@meteora-ag/dlmm')).default;
    } catch (e) {
      const { execSync } = await import('node:child_process');
      execSync('npm init -y >/dev/null 2>&1 || true');
      execSync('npm install @solana/web3.js @meteora-ag/dlmm >/dev/null 2>&1');
      web3 = await import('@solana/web3.js');
      dlmm = (await import('@meteora-ag/dlmm')).default;
    }
    const { Connection, PublicKey } = web3;
    const endpoint = process.env.RPC_PRIMARY || process.env.RPC || 'https://api.mainnet-beta.solana.com';
    const conn = new Connection(endpoint, 'processed');
    const poolKey = new PublicKey(poolAddr);
    const pool = await dlmm.create(conn, poolKey);
    const state = await pool.getPoolState();
    // Try read bins from SDK if exposed
    let bins = [];
    try {
      const nearest = await pool.getActiveBins();
      bins = nearest.map(b => ({ price_x64: b.price.toString(), liq: b.liquidity.toString() }));
    } catch (_) {}
    console.log(JSON.stringify({
      ok:true, type:"meteora_dlmm",
      base_fee_bps: state.baseFeeBps || state.feeBps || 30,
      bins
    }));
  } catch (e) {
    console.error("ERR", e?.message || e);
    process.exit(2);
  }
})();
