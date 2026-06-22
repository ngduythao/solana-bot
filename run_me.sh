#!/usr/bin/env bash
set -euo pipefail
./scripts/install_prereqs.sh
./scripts/setup_wizard.sh
./scripts/start.sh auto
