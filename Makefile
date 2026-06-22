SHELL := /bin/bash
compose := docker compose -f docker-compose.yml
.PHONY: check dirs config run-min run-all stop logs restart clean
check:
	./bin/check.sh
dirs:
	./bin/ensure_dirs.sh
config:
	$(compose) config
run-min: check dirs
	$(compose) up -d redis dashboard metrics-exporter
run-all: check dirs
	$(compose) up -d
stop:
	$(compose) down
logs:
	$(compose) logs --tail=200
restart:
	$(compose) down
	$(compose) up -d
clean:
	rm -rf analytics/* grafana/* prometheus/* || true
