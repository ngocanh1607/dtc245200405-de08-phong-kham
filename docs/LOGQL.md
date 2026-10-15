# Truy vấn LogQL theo đúng cấu hình dự án

Explore → Loki → Last 15 minutes. Thực hiện thao tác web để có log mới. Labels ở đây khớp monitoring/promtail.yml, không dùng label container/service nếu chưa cấu hình chúng.

1. Toàn bộ request Nginx:

```logql
{job="nginx"}
```

2. Lọc 5xx từ JSON access log (tạo lỗi demo khi đã đăng nhập admin):

```logql
{job="nginx"} | json | __error__="" | status >= 500
```

3. Lọc sự kiện lỗi ứng dụng:

```logql
{job="webapp"} | json | __error__="" | level="ERROR"
```

4. Đăng nhập thất bại:

```logql
{job="webapp"} | json | __error__="" | event="login_failed"
```

5. Đếm request 5xx trong 5 phút:

```logql
sum(count_over_time({job="nginx"} | json | __error__="" | status >= 500 [5m]))
```

6. Log PostgreSQL:

```logql
{job="postgres"}
```

Chụp ít nhất 3 query có kết quả: Nginx tất cả request, Nginx 5xx và ứng dụng ERROR. Với query số 4, thử sai mật khẩu một lần trước. Nếu query rỗng kiểm tra khoảng thời gian và labels; rỗng không tự động nghĩa là hệ thống hỏng. Không dùng câu query lỗi cú pháp trong mẫu báo cáo (`|= "HTTP/1.1" 5"`). Query cần khớp định dạng JSON log đang dùng.
