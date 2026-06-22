#!/usr/bin/env bash
set -euo pipefail
echo "[audit] pip check"
pip --version || true
pip check || true
echo "[audit] npm audit (if applicable)"
npm -v && npm audit || true
echo "[audit] cargo update check (if applicable)"
cargo -V && cargo update -Z minimal-versions || true
echo "[audit] DEX program/layout drift smoke test (placeholder)"
# TODO: call a small script to read a known pool account and ensure offsets match
