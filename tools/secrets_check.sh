
#!/usr/bin/env bash
set -euo pipefail
if [ ! -f /opt/solbot/keys/id.json.gpg ]; then
  echo "[!] Missing /opt/solbot/keys/id.json.gpg (GPG-encrypted key). Use setup_wizard.sh to encrypt your id.json."
  exit 1
fi
echo "[✓] Found encrypted key at /opt/solbot/keys/id.json.gpg"
