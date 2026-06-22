
#!/usr/bin/env bash
set -euo pipefail
CPUS="${CPUS:-2,3}"  # example isolated CPUs
cat <<EOF
[isolcpus GUIDE]
1) Edit /etc/default/grub and append to GRUB_CMDLINE_LINUX:
   GRUB_CMDLINE_LINUX="... isolcpus=${CPUS} nohz_full=${CPUS} rcu_nocbs=${CPUS}"
2) Run: sudo update-grub
3) Reboot
4) After reboot, pin critical services using RUN_FAST.sh with CPUS matching isolated set.
EOF
