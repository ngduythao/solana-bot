
#!/usr/bin/env bash
set -euo pipefail
# Requires: awscli configured with credentials (`aws configure`)
DEST="/var/backups/solbot"
BUCKET="${S3_BUCKET:-}"
if [[ -z "$BUCKET" ]]; then echo "Set S3_BUCKET env"; exit 1; fi
echo "[S3] Uploading latest snapshots to s3://$BUCKET/solbot/"
aws s3 sync "$DEST" "s3://$BUCKET/solbot/" --only-show-errors
echo "[S3] Done."
