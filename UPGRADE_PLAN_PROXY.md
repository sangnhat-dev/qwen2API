# Kế hoạch Nâng cấp Hệ thống Proxy cho Qwen2API
**Dựa trên phân tích so sánh: `sangnhat-dev/qwen2API` vs `Rfym21/Qwen2API`**

---

## 🎯 Mục tiêu chính
Triển khai cơ chế **Proxy theo từng tài khoản (Per-Account Proxy)** và **Cơ chế nghỉ tạm thời thông minh (Smart Cooldown)** để:
1. Ngăn chặn việc "chết chùm" khi một IP bị chặn ảnh hưởng đến toàn bộ pool.
2. Tự động cách ly các tài khoản gặp lỗi mạng liên tiếp.
3. Tăng tính ổn định và khả năng mở rộng cho hệ thống production.

---

## 📅 Lộ trình thực hiện (4 Giai đoạn)

### Giai đoạn 1: Chuẩn hóa Cấu trúc Dữ liệu (Data Model)
*Mục tiêu: Mở rộng đối tượng `Account` để lưu trữ thông tin proxy và trạng thái cooldown.*

#### 1.1. Cập nhật Class `Account` (`pool_core.py`)
- **Hành động:** Thêm các trường mới vào class `Account`.
- **Chi tiết kỹ thuật:**
    ```python
    class Account:
        def __init__(self, ..., proxy: Optional[str] = None):
            # ... existing fields ...
            
            # 1. Proxy Configuration
            self.proxy: Optional[str] = proxy  # Format: http://user:pass@ip:port hoặc socks5://...
            self.proxy_type: str = "http"      # http, https, socks5
            
            # 2. Enhanced Error Tracking & Cooldown
            self.consecutive_failures: int = 0
            self.last_error_code: Optional[str] = None
            self.last_error_at: Optional[float] = None
            self.cooldown_started_at: Optional[float] = None
            self.cooldown_duration: float = 300.0  # 5 phút mặc định
            
            # 3. Stats History (Optional - cho tương lai)
            self.stats_history: Dict[str, Dict] = {} 
    ```

#### 1.2. Cập nhật Parser cấu hình (`config_loader.py` hoặc nơi parse env)
- **Hành động:** Hỗ trợ cú pháp mới trong biến môi trường `ACCOUNTS`.
- **Cú pháp đề xuất:** `email:password|proxy_url`
    - Ví dụ: `user1:pass1|http://proxy1.com:8080,user2:pass2|socks5://user:pass@proxy2:1080,user3:pass3` (không proxy)
- **Logic:** Tách chuỗi bằng dấu `|` để lấy proxy, nếu không có thì để `None`.

---

### Giai đoạn 2: Triển khai Logic Quản lý Proxy & Cooldown
*Mục tiêu: Tích hợp proxy vào HTTP Client và xử lý logic nghỉ khi gặp lỗi.*

#### 2.1. Tích hợp Proxy vào HTTP Client (`adapter.py` hoặc `client_factory.py`)
- **Hành động:** Truyền tham số `proxy` vào `httpx.AsyncClient` khi khởi tạo session cho mỗi account.
- **Code mẫu:**
    ```python
    import httpx

    async def create_client(account: Account):
        proxies = None
        if account.proxy:
            proxies = {"http://": account.proxy, "https://": account.proxy}
        
        client = httpx.AsyncClient(
            proxies=proxies,
            timeout=60.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        return client
    ```

#### 2.2. Implement Smart Cooldown Logic (`pool_acquire.py`)
- **Hành động:** Viết hàm `handle_request_error` để cập nhật trạng thái và kiểm tra điều kiện kích hoạt cooldown.
- **Logic:**
    1. Khi request thất bại: Tăng `consecutive_failures`, cập nhật `last_error_at`, `last_error_code`.
    2. Kiểm tra: Nếu `consecutive_failures >= 3` VÀ `cooldown_started_at` chưa được set -> Kích hoạt cooldown (set thời gian bắt đầu).
    3. Khi request thành công: Reset `consecutive_failures` về 0, xóa `cooldown_started_at`.

- **Hàm kiểm tra trạng thái sẵn sàng:**
    ```python
    def is_account_available(account: Account) -> bool:
        if not account.cooldown_started_at:
            return True
        
        # Kiểm tra xem đã hết thời gian cooldown chưa
        if time.time() > account.cooldown_started_at + account.cooldown_duration:
            # Hết cooldown -> Reset trạng thái và cho phép dùng lại
            account.cooldown_started_at = None
            account.consecutive_failures = 0
            return True
        
        return False  # Vẫn đang trong thời gian phạt
    ```

#### 2.3. Cập nhật vòng lặp chọn Account (`acquire_strategy.py`)
- **Hành động:** Lọc bỏ các account đang trong trạng thái `is_account_available() == False` trước khi chọn.

---

### Giai đoạn 3: Tối ưu hóa & Thống kê (Optional nhưng khuyến nghị)
*Mục tiêu: Giảm tải Redis và lưu trữ lịch sử sử dụng.*

#### 3.1. Redis Lazy Connect (Nếu dự án đang dùng Redis)
- **Hành động:** Cấu hình lại connection pool.
- **Tham số:** `lazy_connect=True`, `socket_connect_timeout=5`, `health_check_interval=30`.
- **Lợi ích:** Tránh lỗi kết nối khi Redis chưa sẵn sàng, tự động ngắt kết nối khi idle > 5 phút.

#### 3.2. Tool Schema Compression (`adapter.py`)
- **Hành động:** Viết utility function chuyển đổi JSON Schema phức tạp sang định dạng TypeScript signature ngắn gọn trước khi gửi vào prompt.
- **Lợi ích:** Tiết kiệm token đầu vào, giảm chi phí và độ trễ.

---

### Giai đoạn 4: Kiểm thử & Triển khai
*Mục tiêu: Đảm bảo tính ổn định trước khi đưa vào production.*

#### 4.1. Kịch bản Test (Test Cases)
1. **Test Proxy riêng biệt:**
   - Config 2 accounts với 2 proxy khác nhau (1 good, 1 bad).
   - Verify: Account dùng proxy bad bị fail nhưng không làm ảnh hưởng thread của account proxy good.
   - Check log xem IP request đi ra có đúng với proxy config không.
   
2. **Test Cooldown:**
   - Giả lập lỗi network liên tiếp (3 lần) cho 1 account.
   - Verify: Account đó bị loại khỏi pool trong 5 phút.
   - Sau 5 phút, verify account được tự động đưa trở lại pool.
   - Gửi 1 request thành công -> Verify counter `consecutive_failures` reset về 0.

3. **Test Parse Config:**
   - Test các format: có proxy, không proxy, proxy sai định dạng.

#### 4.2. Deploy
- Cập nhật biến môi trường trên server/prod.
- Monitor logs trong 24h đầu tiên để quan sát tỷ lệ trigger cooldown.

---

## 🛠 Các file cần sửa đổi (Dự kiến)

| File | Mức độ thay đổi | Nội dung chính |
|------|-----------------|----------------|
| `src/models/pool_core.py` | 🔴 Cao | Thêm fields vào class `Account` |
| `src/utils/config_loader.py` | 🟠 Trung bình | Update logic parse string `ACCOUNTS` |
| `src/adapters/qwen_adapter.py` | 🟠 Trung bình | Inject proxy vào `httpx.Client` |
| `src/pool/pool_acquire.py` | 🔴 Cao | Implement logic `is_account_available`, `mark_error` |
| `src/main.py` | 🟢 Thấp | (Nếu cần) Khởi tạo lại clients khi reload config |

---

## ⚠️ Lưu ý quan trọng
1. **Bảo mật:** Không log thông tin nhạy cảm của proxy (password) ra console/file log.
2. **Tương thích ngược:** Đảm bảo parser vẫn hoạt động nếu người dùng chỉ nhập `email:pass` (không có proxy).
3. **Hiệu năng:** Việc kiểm tra `is_account_available` phải cực nhanh (O(1)), tránh làm chậm quá trình chọn account.

---

## ✅ Checklist hoàn thành
- [ ] Cập nhật Class Account
- [ ] Update Config Parser
- [ ] Implement Proxy Injection
- [ ] Implement Cooldown Logic
- [ ] Viết Unit Test cho Cooldown
- [ ] Test thực tế với Proxy thật
- [ ] Deploy lên môi trường Staging
- [ ] Deploy Production
