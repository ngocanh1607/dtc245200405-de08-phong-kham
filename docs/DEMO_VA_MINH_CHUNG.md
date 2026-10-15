# Kịch bản demo và minh chứng chấm điểm

Đọc README và chạy hệ thống trước. Không ghi “thành công” trong báo cáo cho phần chưa kiểm tra. Dùng dữ liệu giả, tránh chụp mật khẩu .env và hồ sơ thật.

| Tiêu chí | Điểm tối đa | Cần demo | Ảnh minh chứng |
| --- | ---: | --- | --- |
| GitHub | 1.5 | Repository source/config, README, 3 commit có ý nghĩa | Cây file, README, lịch sử commit |
| Web + DB | 1.5 | Đăng nhập, thêm bệnh nhân, đặt lịch, dữ liệu xuất hiện trong pgAdmin | Website và SELECT các bảng |
| Nginx | 1.5 | Truy cập qua :8080, curl headers, không publish webapp :8000 | Headers, compose port mapping |
| Metrics | 1.5 | Targets UP, pg_up/nginx_up=1, dashboard container/web/DB | Targets + dashboard đủ 3 lớp |
| Logs | 1.5 | Loki/Promtail hoạt động, ít nhất 3 query có kết quả | Query và log hiển thị |
| Hardening | 1.5 | Non-root, quyền DB, internal network, mật khẩu, headers | id, role query, compose và curl |
| Tổng thể | 1.0 | docker compose chạy hoàn chỉnh, giải thích được kiến trúc | compose ps, sơ đồ, kiểm tra backup |

## Trình tự demo 8–10 phút

1. **1 phút:** giới thiệu đề 8, kiến trúc và Docker Compose. Show repository + commit history. Nói đúng “ứng dụng monolith container hóa cùng các dịch vụ hạ tầng”.
2. **2 phút:** đăng nhập admin → thêm bệnh nhân giả → đặt lịch ngày mai lúc 09:00 → đặt lại cùng ca để show báo xung đột → hủy rồi đặt lại. Trong pgAdmin chạy SELECT để chứng minh persistence.
3. **1 phút:** show `curl -I http://localhost:8080/login`, giải thích Nginx chuyển tiếp tới webapp:8000, port 8000 không publish; headers có always nên cả lỗi cũng có header.
4. **2 phút:** Prometheus targets, Grafana dashboard. Tạo vài request trước khi demo. Giải thích CPU đo qua cAdvisor, Nginx qua exporter/stub_status, DB qua postgres-exporter và pg_monitor. Chỉ rõ 3 loại metrics; không chỉ show Grafana đăng nhập.
5. **2 phút:** bấm lỗi demo 503 bằng admin. Explore Loki show log Nginx, lọc status >=500 và ERROR app. Giải thích labels, pipeline json và khoảng thời gian. Show AppServerErrors firing nếu đã scrape.
6. **1 phút:** show UID10001, DB roles không superuser, DB không có host port, .env không có trong Git; nêu cAdvisor privileged là ngoại lệ.
7. **1 phút:** backup và restore sang DB thử, kết luận các yêu cầu đã kiểm tra thực tế. Không hứa “bảo mật tuyệt đối”.

## SQL để xem trong pgAdmin

```sql
SELECT id, name, phone, birth_date FROM patients ORDER BY id;
SELECT id, name, specialty FROM doctors ORDER BY id;
SELECT a.id, p.name AS patient, d.name AS doctor, a.starts_at, a.status
FROM appointments a
JOIN patients p ON p.id=a.patient_id
JOIN doctors d ON d.id=a.doctor_id
ORDER BY a.id;
```

## Danh sách ảnh nên chụp

1. Cấu hình VM, phiên bản Docker và Compose.
2. Sơ đồ kiến trúc (tự vẽ dựa theo file compose).
3. GitHub cây thư mục.
4. GitHub 3 commit.
5. Trang README hướng dẫn.
6. `docker compose ps`, các service chạy.
7. Website danh sách bệnh nhân và lịch khám.
8. Thông báo chặn trùng lịch.
9. pgAdmin kết nối db và dữ liệu bảng.
10. Nginx security headers.
11. Prometheus targets.
12. Grafana CPU/RAM container.
13. Grafana Nginx và app requests/latency.
14. Grafana PostgreSQL.
15. Query Nginx logs.
16. Query 5xx logs.
17. Query app ERROR.
18. UID và quyền DB.
19. Network isolation và danh sách published ports.
20. Sao lưu + số bản ghi DB phục hồi thử.

Mỗi hình ghi số, caption, thao tác tạo ra kết quả và điều kết quả chứng minh. Không dán ảnh mà không phân tích. Có thể ghép 2 ảnh liên quan trong cùng trang nếu chữ vẫn đọc được.
