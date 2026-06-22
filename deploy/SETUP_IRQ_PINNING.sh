
#!/usr/bin/env bash
set -euo pipefail
if [[ "$EUID" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi
IFACE="${IFACE:-$(ip -o -4 route show to default | awk '{print $5}' | head -n1)}"
CPUMASK="${CPUMASK:-1}"   # hex bitmask; 1=CPU0, 3=CPU0-1, etc
echo "[IRQ] Interface=$IFACE  cpumask=$CPUMASK"
for f in /proc/irq/*/; do
  dev=$(basename "$f")
  if grep -q "$IFACE" "$f"/affinity_hint 2>/dev/null || grep -q "$IFACE" "$f"/../irq/*/hints 2>/dev/null; then
    echo "$CPUMASK" > "$f/smp_affinity" || true
  fi
done
echo "[IRQ] Applied. Consider isolcpus for stronger pinning (requires reboot)."
