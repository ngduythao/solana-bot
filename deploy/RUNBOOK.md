
# Runbook — common incidents
1. RPC dead: bot auto-rotate. Check dashboard RPC panel.
2. Relay down: watchdog restarts. Tip-curve auto adjusts.
3. Disk full: cleanup /var/log, rotate snapshots.
4. Latency spikes: check /pro tip-curve + land-lat feed.
5. Drawdown > limit: compounder auto decompound. Pause trading if needed.

# Chaos kit (simulate faults)
- POWER_FAIL_SIM.sh: test reboot resilience.
- CHAOS_NET.sh: flap network for 10s.
- CHAOS_RPC.sh: kill RPC endpoint, bot rotates.
