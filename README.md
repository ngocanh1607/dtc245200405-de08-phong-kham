# Đề 8 Hệ thống quản lý phòng khám

Ứng dụng học tập quản lý bệnh nhân, bác sĩ, lịch khám. Mục tiêu là triển khai và quản trị đủ các thành phần theo đề môn học. Không có chức năng chẩn đoán hay kê đơn. Dữ liệu seed là dữ liệu giả.

## Chạy lần đầu trên Ubuntu

Máy đề xuất: Ubuntu 22.04/24.04 trên VMware, 4 vCPU, RAM 8 GB, ổ đĩa còn ít nhất 20 GB. Đây là mức gợi ý cho toàn bộ stack; không phải yêu cầu chính thức của đề. Docker Desktop có thể chạy phần web nhưng cAdvisor phụ thuộc môi trường Linux của Docker, nên Ubuntu thuận tiện hơn cho demo giám sát container.

1. Cài Docker Engine và Docker Compose plugin theo tài liệu chính thức: https://docs.docker.com/engine/install/ubuntu/. Kiểm tra `docker --version` và `docker compose version`. Nếu cần dùng sudo cho Docker, thêm sudo trước các lệnh Docker; quyền nhóm docker tương đương quyền quản trị máy.
2. Giải nén, mở terminal tại thư mục `clinic-lab` (nơi chứa `compose.yml`).
3. Chạy:

```bash
python3 scripts/setup_env.py
docker compose config --quiet
docker compose up -d --build
docker compose exec webapp flask --app server seed
docker compose ps
```

Lần đầu tải nhiều image nên có thể mất vài phút. Nếu `webapp` chưa healthy, chờ rồi chạy seed lại. Script seed chạy lặp lại được, không đổi mật khẩu tài khoản đã tồn tại.

## Địa chỉ truy cập

| Thành phần | Địa chỉ trên máy chạy Docker | Đăng nhập |
| --- | --- | --- |
| Website qua Nginx | http://localhost:8080 | admin hoặc letan; mật khẩu ADMIN_PASSWORD / RECEPTION_PASSWORD trong .env |
| pgAdmin | http://localhost:5050 | PGADMIN_EMAIL / PGADMIN_PASSWORD |
| Grafana | http://localhost:3000 | admin / GRAFANA_PASSWORD |
| Prometheus | http://localhost:9090 | Chỉ bind loopback, không có đăng nhập |

Mở `.env` bằng trình soạn thảo riêng để lấy mật khẩu; không chụp màn hình mật khẩu, không commit file này. Các cổng chỉ bind 127.0.0.1. Nếu Docker chạy trong VMware, mở trình duyệt bên trong Ubuntu. Từ Windows có thể dùng SSH tunnel nếu VM đã cài SSH:

```bash
ssh -L 8080:127.0.0.1:8080 -L 3000:127.0.0.1:3000 -L 5050:127.0.0.1:5050 -L 9090:127.0.0.1:9090 TEN_USER@IP_VM
```

Giữ cửa sổ SSH mở rồi truy cập localhost trên Windows. Không cần mở database ra mạng LAN.

## Chức năng website

- Admin và lễ tân đăng nhập bằng mật khẩu được băm, phiên đăng nhập tối đa 4 giờ.
- Thêm, xem, sửa bệnh nhân; admin có thể xóa bệnh nhân chưa có lịch khám.
- Xem danh sách bác sĩ và chuyên khoa; admin thêm bác sĩ.
- Đặt ca khám 30 phút, 08:00–16:30, ở tương lai, giờ Việt Nam.
- Không cho bác sĩ hoặc bệnh nhân nhận hai lịch trong cùng ca. UNIQUE INDEX có điều kiện xử lý xung đột tại PostgreSQL, kể cả hai yêu cầu đồng thời.
- Chuyển lịch đã đặt sang hoàn thành/hủy. Lịch hủy cho phép đặt lại ca đó.
- Không xóa bệnh nhân có lịch khám để giữ lịch sử.

## Kết nối pgAdmin

Sau khi đăng nhập: **Add New Server** → General đặt tên `Clinic PostgreSQL` → Connection:

| Trường | Giá trị |
| --- | --- |
| Host name/address | db |
| Port | 5432 |
| Maintenance database | clinic |
| Username | clinic_app |
| Password | APP_DB_PASSWORD trong .env |

`db` là tên dịch vụ Compose; không nhập localhost vì pgAdmin nằm trong container khác. Dùng clinic_app để xem dữ liệu nghiệp vụ. Chỉ dùng postgres khi cần quản trị; ứng dụng không sử dụng tài khoản superuser.

## Giám sát và log

Grafana → Dashboards → **Clinic Lab → Clinic • Hệ thống phòng khám**. Dashboard đã provision tự động, gồm targets, CPU/RAM container, request/latency ứng dụng, connections Nginx và transactions/connections PostgreSQL. Chờ 2–3 phút và thao tác website để biểu đồ rate có dữ liệu.

Prometheus → Status → Target health: 5 jobs `prometheus`, `webapp`, `nginx`, `postgres`, `containers` phải UP. Targets UP chưa đủ: cần kiểm tra `nginx_up=1`, `pg_up=1` và biểu đồ cAdvisor có tên dịch vụ. Exporter có thể UP nhưng không kết nối được thành phần được giám sát.

Grafana → Explore → chọn **Loki** → khoảng thời gian Last 15 minutes → chạy các query trong `docs/LOGQL.md`. Log được đọc từ named volume chung, không cần mount Docker socket cho Promtail. Thu thập log ứng dụng, Nginx và PostgreSQL; không tuyên bố thu thập stdout của toàn bộ stack.

## Kiểm tra trước demo

```bash
sh scripts/check.sh
docker compose exec -T webapp python < scripts/test_db_concurrency.py
sh scripts/backup.sh
```

`check.sh` có thể báo Loki chưa ready ngay sau khi khởi động; đợi khoảng 30 giây rồi chạy lại. Kiểm tra concurrent booking cần giai đoạn 1 trở lên đã seed; tạo dữ liệu thử và tự dọn sau kiểm tra.

Kiểm tra cảnh báo: Prometheus → Alerts. Đăng nhập admin website, bấm **Tạo lỗi demo 503** rồi đợi 1–2 chu kỳ scrape. `AppServerErrors` sẽ firing. `TargetDown` chỉ kiểm tra target không scrape được; không thay thế kiểm tra `pg_up`/`nginx_up`. Chưa cấu hình gửi email/Telegram vì đề không yêu cầu.

## Bảo mật được triển khai

1. Webapp UID 10001; Nginx UID 101; Grafana, Loki, Promtail, Prometheus có user cụ thể.
2. DB không publish cổng, nằm trong network internal; các giao diện quản trị chỉ mở loopback.
3. clinic_app không có superuser/CREATE DATABASE/CREATE ROLE/CREATE schema. Monitor chỉ có quyền pg_monitor, không dùng mật khẩu DB admin.
4. Mật khẩu và SECRET_KEY ngẫu nhiên trong .env, quyền file 600 trên Linux, được .gitignore loại khỏi Git.
5. HTTP security headers: CSP, X-Frame-Options, nosniff, Referrer-Policy; /metrics bị chặn ở cổng web Nginx.
6. CSRF cho POST, escaping HTML của Jinja, SQL tham số hóa, giới hạn dữ liệu đầu vào; Nginx rate limit đăng nhập.
7. Webapp và Nginx read-only filesystem, tmpfs /tmp, drop capabilities; phần lớn service no-new-privileges.
8. App và access log không ghi nội dung form hoặc thông tin bệnh nhân; PostgreSQL không log câu SQL, lỗi dùng verbosity terse.

**Giới hạn cần giải thích:** Nginx đang dùng HTTP + security headers đúng lựa chọn cho phép trong đề, chưa mã hóa HTTP. Cookie Secure đang false để chạy HTTP; nếu triển khai HTTPS phải chuyển Secure=true. Các image pin phiên bản để tái lập môi trường, không được hiểu là phiên bản mới nhất hoặc đã được quét lỗ hổng. cAdvisor cần privileged và mount filesystem host để thu metrics; đây là ngoại lệ cho VM học tập. init-permissions dùng root một lần để chuẩn bị volume; PostgreSQL image khởi động qua entrypoint và tiến trình DB chạy postgres. Không tuyên bố toàn bộ container non-root, chống leo thang đặc quyền tuyệt đối, hoặc mô hình này là microservices nghiệp vụ (đây là ứng dụng monolith cùng các dịch vụ hạ tầng).

Promtail đã EOL ngày 02/03/2026 theo Grafana. Bài dùng Promtail để đáp ứng đề; hướng nâng cấp là Grafana Alloy. Tham khảo: https://grafana.com/docs/loki/latest/send-data/promtail/.

## GitHub và ba mốc triển khai

Tạo tài khoản/tên theo MSSV theo yêu cầu giảng viên, tạo repository `MSSV-de08-phong-kham`. Không tạo commit rỗng để đủ số lượng. Ba giai đoạn bên dưới thay đổi thật danh sách dịch vụ chạy và datasource Grafana.

```bash
git init
git branch -M main
python3 scripts/select_stage.py 1
docker compose up -d --build --remove-orphans
docker compose exec webapp flask --app server seed
# Kiểm tra website, pgAdmin và security headers rồi commit
git add .gitignore .env.example README.md app db nginx compose.yml scripts stages tests docs
git commit -m "feat: deploy clinic PostgreSQL pgAdmin and Nginx with hardening"

python3 scripts/select_stage.py 2
docker compose up -d --build --remove-orphans
# Kiểm tra targets và dashboard metrics rồi commit
git add compose.yml monitoring/prometheus.yml monitoring/alerts.yml monitoring/grafana
git commit -m "feat: add Prometheus exporters cAdvisor and Grafana dashboard"

python3 scripts/select_stage.py 3
docker compose up -d --build --remove-orphans
# Restart Grafana để nạp datasource Loki mới
docker compose restart grafana
# Kiểm tra LogQL và lưu minh chứng rồi commit
git add compose.yml monitoring
git commit -m "feat: integrate Loki Promtail and centralized log queries"

git remote add origin https://github.com/TEN_GITHUB/MSSV-de08-phong-kham.git
git push -u origin main
git log --oneline
git ls-files .env
```

Lệnh cuối phải không in gì. ZIP giao ở giai đoạn 3; dùng select_stage khi muốn đi từng bước học và tạo lịch sử commit thật. Không có repository online được tạo tự động. Screenshot không cần lên Git nếu chứa thông tin cá nhân; nếu muốn lưu ảnh dữ liệu giả hãy tạo thư mục docs/screenshots và kiểm tra trước khi commit.

## Sao lưu và phục hồi

`sh scripts/backup.sh` tạo bản pg_dump dạng custom dưới backups/ (không lên Git). Lưu một bản ngoài VM. Muốn kiểm chứng backup, restore sang DB thử, không ghi đè DB chính:

```bash
docker compose exec db createdb -U postgres clinic_restore_test
docker compose exec -T db pg_restore -U postgres -d clinic_restore_test --no-owner --no-acl < backups/TEN_FILE.dump
docker compose exec db psql -U postgres -d clinic_restore_test -c 'SELECT count(*) FROM patients;'
```

Chỉ chạy createdb một lần cho DB thử. Việc đổi .env không đổi password bên trong PostgreSQL đã tồn tại; cần đổi bằng SQL quản trị và đồng bộ cấu hình. Không dùng `docker compose down -v` để chữa lỗi thông thường vì sẽ xóa toàn bộ named volumes gồm dữ liệu DB.

## Trạng thái kiểm chứng của bộ dự án

Mã nguồn được kiểm tra bằng pytest với SQLite thử nghiệm: xác thực/CSRF/phân quyền, nhập liệu/sửa bệnh nhân, trùng lịch/hủy lịch/giữ lịch sử, escaping HTML, metrics và lỗi demo. Có script concurrency dành cho PostgreSQL thật trên máy triển khai. Cấu hình YAML/JSON và shell được kiểm tra tĩnh. Môi trường tạo bộ dự án không có Docker nên chưa kiểm chứng build image, kết nối PostgreSQL, exporter, LogQL hay dashboard bằng chạy stack thực tế. Phải hoàn tất checklist trên máy bạn trước khi kết luận triển khai thành công trong báo cáo.

Xem hướng dẫn chi tiết: `docs/DEMO_VA_MINH_CHUNG.md`, `docs/KHUNG_BAO_CAO.md`, `docs/BAO_VE.md`, `docs/XU_LY_LOI.md`.
