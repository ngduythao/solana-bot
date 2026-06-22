
#!/usr/bin/env bash
set -euo pipefail
if [[ "$EUID" -ne 0 ]]; then echo "Run with sudo"; exit 1; fi

# 1) SSH hardening
SSHD=/etc/ssh/sshd_config
cp -n "$SSHD" "$SSHD.bak.$(date +%s)" || true
sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' "$SSHD"
sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin no/' "$SSHD"
sed -i 's/^#\?X11Forwarding .*/X11Forwarding no/' "$SSHD"
sed -i 's/^#\?PermitEmptyPasswords .*/PermitEmptyPasswords no/' "$SSHD"
systemctl restart ssh || systemctl restart sshd || true

# 2) Fail2ban
apt-get update -y && apt-get install -y fail2ban ufw
systemctl enable fail2ban --now || true

# 3) UFW baseline (deny all; open ssh + internal metrics if needed)
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ALLOW_SSH_PORT="${SSH_PORT:-22}"
ufw allow "${ALLOW_SSH_PORT}/tcp"
# dashboard/health ports will be managed by FIREWALL_LOCKDOWN.sh
ufw --force enable
echo "[HARDEN] SSH hardened; fail2ban + ufw baseline applied"
