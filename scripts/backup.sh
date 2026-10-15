#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p backups
chmod 700 backups
file="backups/clinic-$(date +%Y%m%d-%H%M%S).dump"
umask 077
docker compose exec -T db pg_dump -U postgres -d clinic -Fc > "$file"
[ -s "$file" ]
printf 'Đã sao lưu: %s\n' "$file"
