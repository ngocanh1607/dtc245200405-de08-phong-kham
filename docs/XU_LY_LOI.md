# Xử lý lỗi theo thứ tự

## Lỗi cấu hình hoặc thiếu biến

Chạy `python3 scripts/setup_env.py` nếu chưa có .env. `docker compose config --quiet` kiểm tra mà không in password đã interpolate. Không gửi output đầy đủ `docker compose config` vì có thể chứa secrets.

## Không truy cập localhost

Nếu chạy trong VM, localhost Windows không phải VM. Dùng trình duyệt trong Ubuntu hoặc SSH tunnel trong README. Kiểm tra `docker compose ps`. Cổng 8080/3000/5050/9090 bị chiếm thì đổi phần host port; không đổi cổng nội bộ exporter tùy ý.

## Database unhealthy hoặc permission denied log

```bash
docker compose logs --tail=80 init-permissions db
```

Stack dùng PostgreSQL image Debian, log directory thuộc UID999; không tự đổi sang alpine vì UID khác. Init SQL chỉ chạy khi volume PostgreSQL mới. Nếu đổi schema cần migration/SQL quản trị, không xóa volume dữ liệu để ép chạy init. Nếu lần đầu lỗi init tạo DB dở dang, kiểm tra từng table/role với psql trước khi sửa; không reset mù.

## Webapp lỗi kết nối hoặc seed

```bash
docker compose logs --tail=80 webapp
docker compose exec webapp flask --app server seed
```

DB password trong .env phải khớp mật khẩu role thực tế. Script setup không ghi đè .env. Password tài khoản web seed chỉ tạo lần đầu; sửa ADMIN_PASSWORD trong .env không đổi hash đã lưu ở bảng users.

## Nginx trả 502/503

Kiểm tra webapp healthy, upstream tên webapp:8000, network frontend. Nút demo chủ động trả 503 không phải lỗi DB. Sau khi recreate webapp có IP khác, restart nginx để cập nhật DNS upstream: `docker compose restart nginx`.

## Grafana báo No data

Kiểm tra datasource rồi Prometheus targets, `nginx_up`, `pg_up`. Chờ 2–3 phút cho rate. Mở website tạo request. Nếu chỉ cAdvisor rỗng, kiểm tra `docker compose logs --tail=80 cadvisor`, host cgroups, `/var/lib/docker` và labels compose. Docker rootless/Docker Desktop có đường dẫn và quyền khác; Ubuntu Docker Engine trong VM là môi trường khuyến nghị. Không thay biểu đồ thật bằng số liệu giả để demo.

## Loki hoặc LogQL không có dữ liệu

```bash
docker compose logs --tail=80 loki promtail
docker compose exec webapp python -c "from pathlib import Path; print([(str(p),p.stat().st_size) for p in Path('/logs').rglob('*.log')])"
```

Kiểm tra Promtail gửi thành công, quyền đọc log, khoảng thời gian Last 15 minutes, labels job đúng. Tạo lỗi bằng admin, không curl POST thiếu CSRF rồi mong nhận 503. Query JSON status áp dụng Nginx access log, không áp dụng error log dạng text. Không log form bệnh nhân để tạo dữ liệu demo.

## Lỗi 429/503 khi đăng nhập liên tục

Nginx đang rate limit /login, kể cả GET. Dừng gửi liên tục, chờ giới hạn phục hồi. Đây có thể là cơ chế bảo vệ, không phải lỗi mật khẩu. Rate limit Nginx mặc định có thể trả 503 khi vượt giới hạn.

## Dừng và chạy lại

`docker compose stop` dừng tạm, `docker compose start` chạy lại. `docker compose down` xóa containers/networks nhưng giữ named volumes. Không thêm `-v` nếu muốn giữ dữ liệu. Backup trước mọi thao tác thay đổi DB lớn.
