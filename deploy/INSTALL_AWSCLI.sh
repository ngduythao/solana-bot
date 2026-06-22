
#!/usr/bin/env bash
set -euo pipefail
if command -v aws >/dev/null 2>&1; then echo "[AWS] CLI already installed: $(aws --version)"; exit 0; fi
apt-get update -y && apt-get install -y unzip curl
curl -sSfL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
unzip -q /tmp/awscliv2.zip -d /tmp
sudo /tmp/aws/install
echo "[AWS] Installed. Run 'aws configure' to set credentials."
