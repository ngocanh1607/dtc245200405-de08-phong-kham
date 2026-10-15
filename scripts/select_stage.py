#!/usr/bin/env python3
"""Change runtime composition for three real implementation milestones."""
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
if len(sys.argv)!=2 or sys.argv[1] not in ('1','2','3'):
    raise SystemExit('Usage: python3 scripts/select_stage.py 1|2|3')
stage=sys.argv[1]
(root/'compose.yml').write_bytes((root/'stages'/f'compose.stage{stage}.yml').read_bytes())
source='''apiVersion: 1
datasources:
  - name: Prometheus
    uid: prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
'''
if stage=='3':
    source+='''  - name: Loki
    uid: loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
'''
(root/'monitoring/grafana/provisioning/datasources/sources.yml').write_text(source)
print('Đã chọn giai đoạn '+stage+'. Chạy docker compose up -d --build --remove-orphans.')
