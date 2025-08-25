# Test Bot - Không hiển thị nút sau giao dịch

## Cách test:

1. **Gửi `/start`** - Sẽ hiển thị menu với các nút
2. **Nhập `+1000`** - Sẽ hiển thị thông báo thành công KHÔNG có nút
3. **Nhập `-500`** - Sẽ hiển thị thông báo thành công KHÔNG có nút
4. **Gửi `/start`** - Để hiển thị lại menu

## Kết quả mong đợi:

✅ **Sau giao dịch:** Chỉ hiển thị thông báo, không có nút
✅ **Sau `/start`:** Hiển thị menu với các nút
✅ **Ô nhập tin nhắn:** Sạch sẽ sau giao dịch

## Lưu ý:

- Bot đã được cập nhật để ẩn keyboard sau giao dịch
- Chỉ hiển thị nút khi gõ `/start`
- Giao diện sạch sẽ và chuyên nghiệp

