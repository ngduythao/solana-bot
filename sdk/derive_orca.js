// Orca Whirlpools discovery via SDK.
// Usage: node derive_orca.js <cluster> <mintA> <mintB>
(async () => {
  const cluster = process.argv[2] || "mainnet-beta";
  const mintA = process.argv[3];
  const mintB = process.argv[4];
  if (!mintA || !mintB) { console.error("Usage: node derive_orca.js mainnet-beta <mintA> <mintB>"); process.exit(1); }
  try {
    let sdk, web3;
    try {
      sdk = await import('@orca-so/whirlpools-sdk');
      web3 = await import('@solana/web3.js');
    } catch (e) {
      const { execSync } = await import('node:child_process');
      execSync('npm init -y >/dev/null 2>&1 || true');
      execSync('npm install @orca-so/whirlpools-sdk @solana/web3.js >/dev/null 2>&1');
      sdk = await import('@orca-so/whirlpools-sdk');
      web3 = await import('@solana/web3.js');
    }
    const { WhirlpoolContext, ORCA_WHIRLPOOL_PROGRAM_ID, buildWhirlpoolClient, PDAUtil } = sdk;
    const { Connection, PublicKey, clusterApiUrl } = web3;
    const endpoint = cluster === "mainnet-beta" ? "https://api.mainnet-beta.solana.com" : clusterApiUrl(cluster);
    const connection = new Connection(endpoint, "processed");
    const ctx = WhirlpoolContext.withProvider(connection, {}, ORCA_WHIRLPOOL_PROGRAM_ID);
    const client = buildWhirlpoolClient(ctx);
    const pools = await client.getPoolsForTokenPair(new PublicKey(mintA), new PublicKey(mintB));
    const outPools = []; const outTickArrays = [];
    for (const p of pools) {
      const data = await p.getData();
      outPools.push({
        address: p.getAddress().toBase58(),
        tickSpacing: data.tickSpacing,
        sqrtPriceX64: data.sqrtPrice.toString(),
        liquidity: data.liquidity.toString(),
        feeRate: data.feeRate,
        tickCurrentIndex: data.tickCurrentIndex
      });
      const startIndex = Math.floor(data.tickCurrentIndex / data.tickSpacing) * data.tickSpacing;
      for (let k=-1;k<=1;k++) {
        const start = startIndex + k*data.tickSpacing*88;
        const pda = PDAUtil.getTickArrayFromTickIndex(ctx.program.programId, data.tickSpacing, start, p.getAddress());
        outTickArrays.push(pda.publicKey.toBase58());
      }
    }
    console.log(JSON.stringify({pools: outPools, tickArrays: Array.from(new Set(outTickArrays))}));
  } catch (e) { console.error("ORCA_DERIVE_ERROR", e?.message || e); process.exit(2); }
})();
