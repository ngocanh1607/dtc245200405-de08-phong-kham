# Kết quả kiểm thử và cách chạy lại

Kiểm thử tạo bộ dự án ngày 13/10/2026: 4 tests passed. Backend dùng SQLite thử nghiệm, không thay PostgreSQL trong compose. Có 6 deprecation warnings của date/datetime adapter SQLite Python 3.12, không phải lỗi chức năng.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r app/requirements.txt pytest==8.4.1
pytest tests -q
```

Bao phủ: CSRF thiếu bị 400; chưa đăng nhập chuyển về login; lễ tân không được thêm bác sĩ hoặc tạo lỗi demo; điện thoại sai bị từ chối; sửa bệnh nhân; unique ca bác sĩ/bệnh nhân; hủy cho phép đặt lại; FK giữ lịch sử; HTML được escape; metrics có bộ đếm; healthcheck; demo lỗi 503.

Concurrency test chạy trên PostgreSQL thật sau triển khai:

```bash
docker compose exec -T webapp python < scripts/test_db_concurrency.py
```

Kết quả mong đợi: một success, một conflict. Test này chưa được chạy trong môi trường tạo dự án vì không có Docker/PostgreSQL. Build image, permissions volumes, exporter, Grafana datasource, Promtail ingestion và LogQL cần kiểm chứng thực tế.
