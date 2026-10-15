# Khung viết báo cáo theo mẫu được cung cấp

Khung này là hướng dẫn điền báo cáo, chưa phải báo cáo đã hoàn thành. Giữ các chương của mẫu Word, bổ sung mục con dưới đây. Thay placeholder bằng thông tin thật; chỉ mô tả kết quả đã kiểm chứng. Mục tiêu 12–16 trang với nội dung và hình rõ ràng, không kéo giãn dòng để đủ trang.

## Bìa và phần đầu khoảng 2 trang

- Tên trường, khoa giữ theo mẫu nếu đúng thông tin của bạn.
- Môn Triển khai và Quản trị Hệ thống Phần mềm.
- Đề 8 Hệ thống quản lý phòng khám.
- Họ tên [điền], MSSV [điền], lớp [điền], giảng viên [điền nếu có], thời gian [điền].
- Mục lục tự động Word; danh mục hình nếu cần.

## Chương 1 khoảng 2 trang

### 1.1 Mục tiêu và phạm vi

Trình bày quản lý bệnh nhân, bác sĩ, lịch khám. Mục tiêu triển khai, giám sát, log và hardening. Phạm vi phần mềm học tập; không chẩn đoán, kê đơn hoặc lưu hồ sơ y tế chuyên sâu.

### 1.2 Kiến trúc và luồng dữ liệu

Vẽ client → Nginx → Flask → PostgreSQL; pgAdmin → PostgreSQL. Prometheus scrape app, Nginx exporter, PostgreSQL exporter, cAdvisor. Grafana query Prometheus/Loki. App/Nginx/PostgreSQL ghi log volume → Promtail → Loki. Kèm bảng port và network từ compose. Giải thích database không publish port và giao diện admin chỉ bind localhost.

### 1.3 Môi trường

Ghi Ubuntu/Windows thực tế, VM RAM/CPU, phiên bản Docker/Compose và image tags từ compose. Chụp lệnh phiên bản. Phân biệt thông số máy thực tế với thông số đề xuất.

### 1.4 GitHub

URL thật, cấu trúc thư mục, README, .gitignore, ý nghĩa 3 commit. Chụp history, không bịa hash commit.

## Chương 2 khoảng 3 trang

### 2.1 Website

Stack Flask + Gunicorn, các chức năng và phân quyền. Mô tả quy trình đăng nhập → tạo bệnh nhân → chọn bác sĩ và ca → đặt lịch → hoàn thành/hủy. Có ảnh giao diện.

### 2.2 PostgreSQL và pgAdmin

Sơ đồ 4 bảng users/patients/doctors/appointments. FK lịch khám tham chiếu bác sĩ, bệnh nhân. Các unique indexes doctor_slot và patient_slot dùng điều kiện status != cancelled. Mô tả tài khoản clinic_app, clinic_monitor. Show pgAdmin và SELECT dữ liệu.

### 2.3 Compose và persistence

Giải thích depends_on/healthcheck, named volumes và log volume; trích đoạn vừa đủ, không dán toàn bộ compose. Show compose ps. Phân biệt restart container giữ dữ liệu với down -v xóa dữ liệu.

### 2.4 Nginx Commit 1

Luồng reverse proxy, cổng 8080 → webapp:8000, các headers, endpoint /metrics chặn ở public server; stub_status ở cổng riêng không publish. Ghi đang dùng HTTP + security headers theo lựa chọn trong đề, không khẳng định HTTPS nếu chưa triển khai.

## Chương 3 khoảng 3–4 trang

### 3.1 Prometheus và Grafana Commit 2

Giải thích scrape 15s; 5 jobs, exporter và cAdvisor. Show targets, pg_up/nginx_up và dashboard. Phân tích số liệu của chính lần demo: CPU/RAM, connections, requests, latency. Không bịa số trước khi có hình. Giải thích p95 là ngưỡng 95% request không vượt quá trong cửa sổ đo.

### 3.2 Cảnh báo

Rule TargetDown, AppServerErrors và cách tạo lỗi demo 503; ảnh Alerts nếu kiểm chứng. Chưa có Alertmanager gửi thông báo ra ngoài.

### 3.3 Loki và Promtail Commit 3

Giải thích log file trên volume → Promtail → Loki → Grafana Explore, labels job. Chụp ít nhất 3 query trong LOGQL.md và giải thích kết quả. Thu log app, Nginx, PostgreSQL; không mô tả Docker socket khi cấu hình không dùng. Ghi Promtail EOL và Alloy trong hướng phát triển.

## Chương 4 khoảng 2–3 trang

### 4.1 Các biện pháp hardening

Lập bảng biện pháp, cấu hình đã dùng, cách kiểm tra và ảnh. Ưu tiên non-root, network internal/no DB port, DB least privilege, .env/Git, security headers, CSRF/escaping/parameterized SQL, filesystem read-only. Ghi đúng ngoại lệ cAdvisor và init-permissions. Non-root giảm tác động khi bị khai thác, không ngăn tuyệt đối mọi leo thang đặc quyền.

### 4.2 Kiểm thử

Bảng tình huống/đầu vào/kết quả mong đợi/kết quả thực tế: đăng nhập đúng/sai, CSRF thiếu, lễ tân thêm bác sĩ bị 403, điện thoại sai/trùng, ca ngoài giờ, trùng bác sĩ, trùng bệnh nhân, hủy và đặt lại, 2 yêu cầu concurrent, xóa bệnh nhân có lịch, dữ liệu sau restart. Điền PASS chỉ sau khi kiểm chứng.

### 4.3 Sao lưu và hạn chế

pg_dump, restore sang database thử, so sánh số bản ghi. Hạn chế HTTP, dữ liệu giả, chưa CI/CD, cAdvisor privileged, Promtail EOL, chưa alert ra ngoài, chưa stress test. Trạng thái kiểm tra ban đầu trong README không thay thế kết quả triển khai thực tế của bạn.

## Kết luận và tài liệu tham khảo khoảng 1 trang

Đối chiếu 6 yêu cầu kỹ thuật, nêu kết quả đã làm. Hướng phát triển HTTPS, Alloy, CI/CD, kiểm tra image, nâng cấp phân quyền và lưu vết nghiệp vụ. Tham khảo tài liệu Docker, Prometheus, Grafana, PostgreSQL, Flask chính thức. Ghi ngày truy cập thật.

## Rà soát trước nộp

Ít nhất 10 trang theo đề; bìa có đề tài và sinh viên; hình đọc được; mục lục cập nhật; URL GitHub và commit thật; query có kết quả; không lộ mật khẩu; không giữ placeholder; báo cáo khớp compose và demo; không sao chép lỗi query hoặc tuyên bố bảo mật quá mức trong mẫu.
