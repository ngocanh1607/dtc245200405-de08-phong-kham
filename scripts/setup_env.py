#!/usr/bin/env python3
import os, secrets
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'.env'
if p.exists():
    raise SystemExit('.env đã tồn tại; giữ nguyên để không mất đồng bộ mật khẩu với DB.')
keys=['POSTGRES_PASSWORD','APP_DB_PASSWORD','MONITOR_DB_PASSWORD','SECRET_KEY','ADMIN_PASSWORD','RECEPTION_PASSWORD','PGADMIN_PASSWORD','GRAFANA_PASSWORD']
p.write_text(''.join(k+'='+secrets.token_hex(24)+'\n' for k in keys)+'PGADMIN_EMAIL=admin@example.com\nENABLE_DEMO=true\n')
os.chmod(p,0o600)
print('Đã tạo .env với mật khẩu ngẫu nhiên. Mở file riêng để lấy mật khẩu; không chia sẻ file này.')
