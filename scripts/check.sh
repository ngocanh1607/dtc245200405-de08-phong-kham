#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
docker compose config --quiet
docker compose ps
curl --fail http://localhost:8080/healthz
printf '\n--- Security headers ---\n'
curl -sI http://localhost:8080/login
printf '\n--- Non-root application ---\n'
docker compose exec -T webapp id
printf '\n--- Application DB privileges ---\n'
docker compose exec -T db psql -U postgres -d clinic -c "SELECT rolname,rolsuper,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname IN ('clinic_app','clinic_monitor');"
printf '\n--- Prometheus targets ---\n'
curl --fail http://localhost:9090/api/v1/targets
printf '\n--- Loki readiness ---\n'
docker compose exec -T webapp python -c "import urllib.request; print(urllib.request.urlopen('http://loki:3100/ready').read().decode())"
