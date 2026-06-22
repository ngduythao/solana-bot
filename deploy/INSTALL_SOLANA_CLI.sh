
#!/usr/bin/env bash
set -euo pipefail
if command -v solana >/dev/null 2>&1; then echo "[SOLANA] CLI already installed: $(solana --version)"; exit 0; fi
curl -sSfL https://release.solana.com/stable/install | sh -s stable
echo 'export PATH="$HOME/.local/share/solana/install/releases/$(ls $HOME/.local/share/solana/install/releases | sort | tail -n1)/solana-release/bin:$PATH"' >> $HOME/.bashrc
echo "[SOLANA] Installed. Re-login or run: export PATH=.../solana-release/bin:$PATH"
