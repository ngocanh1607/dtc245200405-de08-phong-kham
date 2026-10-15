# Câu hỏi bảo vệ thường gặp

**Nginx để làm gì?** Nhận request tại cổng 8080, chuyển đến Gunicorn/Flask bên trong, áp dụng headers và rate limit. Người dùng không truy cập trực tiếp port 8000 của app.

**Prometheus và Grafana khác nhau thế nào?** Prometheus scrape và lưu metrics chuỗi thời gian; Grafana query datasource rồi hiển thị dashboard. Grafana không tự thu CPU container trong mô hình này.

**Exporter dùng để làm gì?** Chuyển số liệu của Nginx/PostgreSQL sang dạng Prometheus có thể scrape. cAdvisor thu số liệu container. Metrics app do prometheus-client tạo.

**Target UP có đồng nghĩa DB tốt không?** Không. UP nghĩa Prometheus scrape được exporter. Cần pg_up=1 và metrics DB; Nginx tương tự với nginx_up.

**Metrics và logs khác nhau thế nào?** Metrics là số liệu tổng hợp như CPU, số request, latency. Log là sự kiện cụ thể, hữu ích để điều tra request lỗi. Prometheus quản metrics; Loki quản logs.

**Hai lễ tân đặt cùng ca thì sao?** PostgreSQL có unique index (doctor_id,starts_at) và (patient_id,starts_at) cho lịch chưa hủy. Hai transaction cạnh tranh, một commit được, một nhận IntegrityError. App rollback và thông báo xung đột. Không chỉ kiểm tra SELECT rồi INSERT vì có race condition. Script test_db_concurrency.py kiểm tra trực tiếp trên PostgreSQL.

**Vì sao không xóa bệnh nhân có lịch?** Foreign key giữ toàn vẹn và tránh mất quan hệ lịch sử. Muốn quản lý lưu trữ dài hạn có thể thêm inactive/soft delete; hiện bài chưa triển khai chức năng đó.

**Tại sao pgAdmin host db mà không localhost?** localhost trong container là chính container pgAdmin. Tên dịch vụ db được Docker DNS phân giải đến container PostgreSQL trên network chung.

**Mật khẩu trong .env đã là secrets manager chưa?** Chưa. .env tách cấu hình khỏi Git, quyền 600 hạn chế đọc trên máy Linux; người có quyền Docker/root vẫn xem được môi trường container. Hệ thống lớn nên dùng secret management phù hợp.

**Có phải mọi container đều non-root không?** Không. App/Nginx và nhiều dịch vụ có user cụ thể; cAdvisor cần quyền rộng để giám sát host; init-permissions dùng root một lần; PostgreSQL official image dùng entrypoint chuẩn. Nêu đúng từng thành phần và ngoại lệ.

**Security headers có thay HTTPS không?** Không. Headers giới hạn hành vi trình duyệt; HTTPS mã hóa và xác thực kênh truyền. Đề cho chọn HTTPS tự ký hoặc headers; bài đang dùng headers. Triển khai thực tế cần TLS.

**Đây có phải microservices không?** Nghiệp vụ phòng khám nằm trong một Flask app, nên là monolith được container hóa cùng các dịch vụ hạ tầng. Nhiều container không tự động biến thành microservices nghiệp vụ.

**Sao vẫn dùng Promtail?** Đề yêu cầu rõ Promtail. Bài thực hành đáp ứng đề và ghi nhận Promtail đã EOL; hướng nâng cấp Alloy. Không khẳng định Promtail còn được bảo trì.

**Cảnh báo đã gửi tin nhắn chưa?** Chưa. Có rule và trạng thái cảnh báo trong Prometheus; muốn gửi email/Telegram cần Alertmanager hoặc cấu hình Grafana Alerting riêng.

**Backup có dùng được không?** Chứng minh bằng restore sang clinic_restore_test, query dữ liệu và đối chiếu. Chỉ có file dump chưa đủ chứng minh phục hồi thành công.
