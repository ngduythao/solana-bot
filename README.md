# Solana Bot

Solana Bot is a research-oriented trading infrastructure project for Solana DEX/CEX arbitrage.

The system focuses on deterministic simulation, paper trading, shadow-mode execution, risk controls, and Redis-based orchestration. Live execution is intentionally gated behind explicit runtime configuration, credentials, allowlists, and risk limits.

> Default posture: simulation / paper / shadow mode.  
> Live trading requires deliberate configuration.

---

## Overview

Solana Bot combines:

- Market and RPC readers
- Opportunity preselection
- CLMM / DLMM swap simulation
- Risk and expected-value filters
- Redis-backed queues
- Orchestration services
- Execution boundaries for Solana / Jupiter integrations
- Inventory, hedge, monitoring, and deployment services

```mermaid
flowchart LR
  A["Market / RPC Readers"] --> B["Preselector"]
  B --> C["CLMM / DLMM Simulator"]
  C --> D["Risk + EV Filters"]
  D --> E["Redis Queues"]
  E --> F["Orchestrator"]
  F --> G["Executors"]
  F --> H["Hedge / Inventory Services"]
  F --> I["Metrics + Alerts"]
  I --> J["Dashboard / Prometheus / Grafana"]
````

---

## Current Status

* **Simulation:** deterministic CLMM / DLMM simulation hooks with focused test coverage.
* **Local stack:** Docker Compose wiring for Redis, dashboard, metrics, and orchestration services.
* **Executor boundary:** Rust crate for Solana / Jupiter-facing integration points.
* **Runtime safety:** paper and shadow-mode defaults, with live paths controlled by environment configuration.

---

## Project Layout

```text
.
├── simulator/          # Deterministic CLMM / DLMM simulation logic
├── tests/              # Focused simulator and service tests
├── orchestrator/       # Redis-driven opportunity routing
├── services/           # Risk, circuit breakers, inventory, fees, monitoring
├── executor/           # Rust execution boundary for Solana / Jupiter
├── deploy/             # Deployment helpers
├── systemd/            # systemd service units
├── docker-compose.yml  # Local stack definition
└── .env.example        # Runtime configuration template
```

---

## Quickstart

### 1. Create local configuration

```bash
cp .env.example .env
mkdir -p secrets analytics certs
```

Create placeholder secret files for local development:

```bash
touch secrets/solana_keypair_hex \
  secrets/binance_api_key \
  secrets/binance_api_secret \
  secrets/bybit_api_key \
  secrets/bybit_api_secret
```

Review `.env` before starting any services.

---

### 2. Validate Docker Compose config

```bash
docker compose -f docker-compose.yml config
```

---

### 3. Start the local stack

```bash
docker compose up -d redis dashboard metrics-exporter
```

Dashboard:

```text
http://127.0.0.1:8080
```

---

## Python Development

Create and activate a virtual environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
```

Install development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install pytest fastapi pydantic httpx
```

Run a Python syntax sanity check:

```bash
python -m compileall -q simulator orchestrator services tests
```

Run tests:

```bash
PYTHONPATH=. pytest -q tests
```

`compileall` only checks that Python files can be compiled to bytecode. It does not build a binary or package the project. It is used here as a lightweight syntax check before running tests.

---

## Rust Executor

Format check:

```bash
cargo fmt --manifest-path executor/Cargo.toml -- --check
```

Type and dependency check:

```bash
cargo check --manifest-path executor/Cargo.toml
```

---

## Verification

The CI pipeline validates:

* Python syntax sanity checks
* Simulator test suite
* YAML linting
* Bash syntax checks
* Docker Compose configuration
* Rust formatting
* Rust executor `cargo check`

---

## Runtime Safety

Live execution is not enabled by default.

Production or live-like execution should require:

* Explicit environment flags
* External exchange credentials
* Solana key material
* Market and token allowlists
* Risk limits
* Circuit breakers
* Monitoring and alerting

This project is designed so that research, simulation, and shadow-mode workflows can run independently from live execution paths.