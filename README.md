# Telegram Bot - Quản lý tiền và phí theo nhóm

Bot Telegram được viết bằng Python sử dụng thư viện python-telegram-bot để quản lý tiền và phí giao dịch với khả năng cài đặt phí riêng cho từng nhóm.

## Tính năng mới

- **Cài đặt phí theo nhóm**: Mỗi nhóm Telegram có thể có mức phí riêng biệt
- **Quản lý dữ liệu theo nhóm**: Dữ liệu được tách biệt cho từng nhóm
- **Giao diện cài đặt**: Nút cài đặt phí với các mức phí phổ biến (1%, 2%, 3%, 5%, 10%, 15%)
- **Lưu trữ cài đặt**: Cài đặt được lưu trong file `settings.json`

## Tính năng cơ bản

- **Kiểm tra quyền admin**: Chỉ admin mới có thể sử dụng bot
- **Cộng tiền**: Gửi tin nhắn bắt đầu bằng "+" để cộng tiền
- **Tính phí tự động**: Phí được tính theo tỷ lệ có thể cài đặt
- **Xem tổng kết**: Lệnh `/summary` để xem tổng tiền và phí
- **Lưu trữ local**: Dữ liệu được lưu trong file `total.json` và `settings.json`

## Cài đặt

### Cài đặt Local

1. **Cài đặt Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Tạo bot Telegram:**
   - Mở Telegram và tìm @BotFather
   - Gửi lệnh `/newbot`
   - Đặt tên cho bot và username
   - Lưu lại token bot được cung cấp

3. **Lấy ID admin:**
   - Gửi tin nhắn cho @userinfobot để lấy ID của bạn
   - Hoặc sử dụng bot @RawDataBot

4. **Cấu hình bot:**
   - Tạo file `.env` từ `.env.example`
   - Cập nhật `BOT_TOKEN` và `ADMIN_IDS` trong file `.env`

### Deploy lên Render

1. **Fork hoặc clone repository này**

2. **Tạo tài khoản Render:**
   - Đăng ký tại [render.com](https://render.com)
   - Kết nối với GitHub/GitLab

3. **Tạo Web Service:**
   - Chọn "New Web Service"
   - Kết nối với repository
   - Chọn branch (thường là `main`)

4. **Cấu hình Environment Variables:**
   - `BOT_TOKEN`: Token bot Telegram của bạn
   - `ADMIN_IDS`: ID admin (có thể nhiều ID, phân cách bằng dấu phẩy)
   - `ENVIRONMENT`: `production`

5. **Cấu hình Build:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`

6. **Deploy:**
   - Click "Create Web Service"
   - Render sẽ tự động build và deploy

## Sử dụng

1. **Khởi động bot:**
   ```bash
   python bot.py
   ```

2. **Các lệnh có sẵn:**
   - `/start` - Khởi động bot và xem hướng dẫn
   - `/summary` - Xem tổng tiền và phí hiện tại
   - `/reset_time` - Xem thời gian reset tự động

3. **Cách cộng tiền:**
   - Gửi tin nhắn bắt đầu bằng "+" (VD: `+1000`)
   - Bot sẽ tự động tính phí theo mức phí của nhóm và cập nhật tổng

4. **Cài đặt phí cho nhóm:**
   - Nhấn nút "⚙️ Cài đặt phí" trong menu
   - Chọn mức phí mong muốn (1%, 2%, 3%, 5%, 10%, 15%)
   - Phí sẽ được áp dụng ngay lập tức cho nhóm hiện tại

## Cấu trúc dữ liệu

### File `total.json`:
```json
{
  "totalAmount": 0,
  "totalFee": 0,
  "transactions": [],
  "transactionCount": 0,
  "group_data": {
    "123456789": {
      "totalAmount": 0,
      "totalFee": 0,
      "transactions": [],
      "transactionCount": 0
    }
  }
}
```

### File `settings.json`:
```json
{
  "global_fee_rate": 0.02,
  "group_settings": {
    "123456789": {
      "fee_rate": 0.05,
      "updated_at": "25/12/2024 15:30:00"
    }
  },
  "default_group_fee_rate": 0.02
}
```

## Ví dụ sử dụng

```
User: /start
Bot: 🤖 BOT QUẢN LÝ TIỀN
     Chọn chức năng bạn muốn sử dụng:
     [📊 Xem báo cáo] [📋 Lịch sử giao dịch]
     [🔄 Reset dữ liệu] [⏰ Thời gian reset]
     [⚙️ Cài đặt phí] [ℹ️ Hướng dẫn]

User: +5000
Bot: 💰 GIAO DỊCH THÀNH CÔNG
     Đã cộng: +5,000
     Tổng tiền hiện tại: 5,000
     Phí giao dịch: 100 (2.0%)

User: [Nhấn ⚙️ Cài đặt phí]
Bot: ⚙️ CÀI ĐẶT PHÍ GIAO DỊCH
     Phí hiện tại: 2.0%
     [1%] [2%] [3%]
     [5%] [10%] [15%]
     [🔙 Quay lại]

User: [Nhấn 5%]
Bot: ✅ ĐÃ CẬP NHẬT PHÍ THÀNH CÔNG
     Phí mới: 5.0%
     Cập nhật lúc: 25/12/2024 15:30:00
```

## Tính năng đặc biệt

### 🔄 **Auto Reset theo nhóm:**
- Dữ liệu của mỗi nhóm được reset riêng biệt lúc 00:00
- Không ảnh hưởng đến dữ liệu của các nhóm khác

### 📊 **Báo cáo theo nhóm:**
- Mỗi nhóm có báo cáo riêng với mức phí tương ứng
- Lịch sử giao dịch được lưu riêng cho từng nhóm

### ⚙️ **Quản lý cài đặt:**
- Cài đặt phí được lưu trữ an toàn
- Có thể thay đổi phí bất cứ lúc nào
- Hiển thị thông tin chi tiết về cài đặt hiện tại

## Lưu ý

- Chỉ admin mới có thể sử dụng bot và thay đổi cài đặt
- Phí được tính tự động theo mức phí của từng nhóm
- Dữ liệu được lưu locally trong file JSON
- Bot hỗ trợ tiếng Việt
- Mỗi nhóm có dữ liệu và cài đặt hoàn toàn độc lập
- Auto reset chỉ ảnh hưởng đến nhóm hiện tại
