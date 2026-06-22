#!/bin/bash

# Local testing mode on macOS

set -e

echo "🍎 Starting Solana Bot on macOS (ARM64)..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p analytics logs reports exports snapshots

# Set up environment for local testing
echo "⚙️  Setting up environment..."
export SIGNER_MODE=paper
export DRY_RUN=true
export SHADOW_MODE=true
export LOG_LEVEL=INFO

# Create a minimal .env file for local testing
cat > .env << EOF
# === macOS Local Testing Configuration ===
REDIS_URL=redis://redis:6379/0
RPC_PRIMARY=https://api.mainnet-beta.solana.com
RPC_FALLBACK_1=https://rpc.solana.wtf/
RPC_FALLBACK_2=https://ssc-dao.genesysgo.net/

# Testing Mode
SIGNER_MODE=paper
DRY_RUN=true
SHADOW_MODE=true
SOLBOT_ENABLED=true

# Risk Management (Conservative for Testing)
RISK_MODE=fixed
RISK_FIXED_PCT=1
RISK_MIN_PCT=0.5
RISK_MAX_DD=2

# Jupiter API
JUP_BASE=https://quote-api.jup.ag

# Logging
LOG_LEVEL=INFO

# CEX (Disabled for Testing)
ENABLE_CEX_TRADING=false

# Fee Management
FEE_BASE_LAMPORTS=5000
FEE_BURN_CAP_PCT=0.3
BANDIT_EPSILON=0.1

# Cross-venue (Disabled for Testing)
CROSS_SIZE_USD=100
CROSS_EV_THR_BPS=5
CROSS_SLIPPAGE_BPS=20
CROSS_ONLY_DIRECT=true

# Hedge Settings
HEDGE_INTERVAL_SEC=300
INVENTORY_SKEW_CAP=0.05
HEDGE_MIN_NOTIONAL_USD=10

# Ops Guard (Conservative)
OPS_RPC_P95_THR=200
OPS_ACCEPT_THR=0.5
OPS_LOSS_CAP=-0.005
EOF

echo "✅ Environment configured for local testing"

# Start with minimal services first
echo "🚀 Starting core services..."
docker compose -f docker-compose.local.yml up -d redis dashboard metrics-exporter

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker compose -f docker-compose.local.yml ps

# Start the orchestrator and other core services
echo "🤖 Starting trading services..."
docker compose -f docker-compose.local.yml up -d orchestrator preselector backrun ai-fee-bandit tuner

# Wait a bit more
sleep 5

echo "✅ Solana Bot is running in local testing mode!"
echo ""
echo "📊 Dashboard: http://localhost:8080"
echo "📈 Metrics: http://localhost:9100"
echo "🔍 Prometheus: http://localhost:9090"
echo "📊 Grafana: http://localhost:3001"
echo ""
echo "📝 Logs: docker compose -f docker-compose.local.yml logs -f"
echo "🛑 Stop: docker compose -f docker-compose.local.yml down"
echo ""
echo "⚠️  Note: Running in PAPER MODE - no real trades will be executed"
echo "⚠️  Note: SHADOW MODE enabled - all actions are logged only"
