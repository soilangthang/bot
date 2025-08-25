import json
import re
import asyncio
import threading
import time
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, CommandHandler, CallbackQueryHandler, Filters, CallbackContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cấu hình bot
BOT_TOKEN = os.getenv("BOT_TOKEN", "8330490898:AAGdH3HayTNQjiuNEqNeIJDvEm1o4UNsrwA")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "8114375011").split(",")]
DEFAULT_FEE_RATE = 0.02  # Mức phí mặc định 2%
TOTAL_FILE = "total.json"
SETTINGS_FILE = "settings.json"

# Khởi tạo file settings.json nếu chưa tồn tại
def init_settings_file():
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {
            "global_fee_rate": DEFAULT_FEE_RATE,
            "group_settings": {},
            "default_group_fee_rate": DEFAULT_FEE_RATE
        }
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    return settings

# Khởi tạo file total.json nếu chưa tồn tại
def init_total_file():
    try:
        with open(TOTAL_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Đảm bảo file có đầy đủ các trường cần thiết
            if "transactions" not in data:
                data["transactions"] = []
            if "transactionCount" not in data:
                data["transactionCount"] = 0
            if "group_data" not in data:
                data["group_data"] = {}
            # Lưu lại file với cấu trúc đầy đủ
            with open(TOTAL_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        data = {
            "totalAmount": 0, 
            "totalFee": 0,
            "transactions": [],
            "transactionCount": 0,
            "group_data": {}
        }
        with open(TOTAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return data

# Đọc dữ liệu từ file
def read_total_data():
    with open(TOTAL_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# Lưu dữ liệu vào file
def save_total_data(data):
    with open(TOTAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Đọc cài đặt từ file
def read_settings():
    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# Lưu cài đặt vào file
def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

# Lấy mức phí cho nhóm cụ thể
def get_fee_rate_for_group(group_id=None):
    settings = read_settings()
    if group_id and str(group_id) in settings["group_settings"]:
        return settings["group_settings"][str(group_id)]["fee_rate"]
    return settings.get("default_group_fee_rate", DEFAULT_FEE_RATE)

# Lấy dữ liệu nhóm
def get_group_data(group_id):
    data = read_total_data()
    group_id_str = str(group_id)
    if group_id_str not in data["group_data"]:
        data["group_data"][group_id_str] = {
            "totalAmount": 0,
            "totalFee": 0,
            "transactions": [],
            "transactionCount": 0
        }
        save_total_data(data)
    return data["group_data"][group_id_str]

# Cập nhật dữ liệu nhóm
def update_group_data(group_id, group_data):
    data = read_total_data()
    data["group_data"][str(group_id)] = group_data
    save_total_data(data)

# Hàm tự động reset dữ liệu lúc 00:00
def auto_reset_daily():
    while True:
        now = datetime.now()
        # Tính thời gian đến 00:00 ngày mai
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        seconds_until_midnight = (tomorrow - now).total_seconds()
        
        print(f"⏰ [AUTO RESET] Sẽ reset lúc 00:00 ngày mai ({seconds_until_midnight/3600:.1f} giờ nữa)")
        
        # Chờ đến 00:00
        time.sleep(seconds_until_midnight)
        
        try:
            # Reset dữ liệu cho tất cả nhóm
            data = read_total_data()
            for group_id in data["group_data"]:
                data["group_data"][group_id] = {
                    "totalAmount": 0,
                    "totalFee": 0,
                    "transactions": [],
                    "transactionCount": 0
                }
            save_total_data(data)
            
            reset_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            print(f"🔄 [AUTO RESET] Đã tự động reset dữ liệu lúc {reset_time}")
            
            # Gửi thông báo cho tất cả admin (sử dụng threading để tránh xung đột)
            def send_notifications():
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    if 'bot_application' in globals():
                        for admin_id in ADMIN_IDS:
                            try:
                                bot_application.bot.send_message(
                                    chat_id=admin_id,
                                    text=f"🔄 *TỰ ĐỘNG RESET*\n\nDữ liệu đã được reset về 0 lúc {reset_time}",
                                    parse_mode='Markdown'
                                )
                            except Exception as e:
                                print(f"❌ Không thể gửi thông báo cho admin {admin_id}: {str(e)}")
                    loop.close()
                except Exception as e:
                    print(f"❌ Lỗi khi gửi thông báo: {str(e)}")
            
            # Chạy thông báo trong thread riêng
            notification_thread = threading.Thread(target=send_notifications)
            notification_thread.start()
                        
        except Exception as e:
            print(f"❌ [AUTO RESET ERROR] Lỗi khi tự động reset: {str(e)}")
        
        # Chờ 1 giây để tránh reset nhiều lần
        time.sleep(1)

# Xử lý tin nhắn văn bản
def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    message_text = update.message.text
    chat_id = update.effective_chat.id
    
    # Kiểm tra quyền admin
    if user_id not in ADMIN_IDS:
        update.message.reply_text("❌ *Bạn không có quyền sử dụng bot này*", parse_mode='Markdown')
        return
    
    # Xử lý tin nhắn bắt đầu bằng "+" hoặc "-"
    if message_text.startswith('+') or message_text.startswith('-'):
        try:
            # Lấy số sau dấu "+" hoặc "-"
            amount_str = message_text[1:].strip()
            amount = int(amount_str)
            
            # Nếu bắt đầu bằng "-" thì chuyển thành số âm
            if message_text.startswith('-'):
                amount = -amount
            
            # Lấy dữ liệu nhóm hiện tại
            group_data = get_group_data(chat_id)
            
            # Kiểm tra nếu trừ tiền thì có đủ tiền không
            if amount < 0 and abs(amount) > group_data["totalAmount"]:
                update.message.reply_text("⚠️ *Lỗi:* Không đủ tiền để trừ!", parse_mode='Markdown')
                return
            
            # Lấy mức phí cho nhóm này
            fee_rate = get_fee_rate_for_group(chat_id)
            
            # Tạo giao dịch mới
            transaction_id = group_data.get("transactionCount", 0) + 1
            current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            # Tính phí (luôn dương)
            fee = int(abs(amount) * fee_rate)
            
            transaction = {
                "id": transaction_id,
                "amount": amount,
                "fee": fee,
                "fee_rate": fee_rate,
                "timestamp": current_time,
                "type": "manual",
                "group_id": chat_id
            }
            
            # Cập nhật dữ liệu nhóm
            group_data["totalAmount"] += amount
            group_data["totalFee"] += fee
            group_data["transactionCount"] = transaction_id
            group_data["transactions"].append(transaction)
            
            # Lưu lại vào file
            update_group_data(chat_id, group_data)
            
            # Xác định loại giao dịch và icon
            if amount > 0:
                action_text = f"💚 **Đã cộng:** `+{amount:,}`"
                transaction_type = "CỘNG TIỀN"
                action_emoji = "💰"
            else:
                action_text = f"🔴 **Đã trừ:** `{amount:,}`"
                transaction_type = "TRỪ TIỀN"
                action_emoji = "💸"
            
            # Gửi phản hồi với format đẹp và chuyên nghiệp
            response = f"""🎯 *GIAO DỊCH THÀNH CÔNG* 🎯

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🆔 *MÃ GIAO DỊCH:* `#{transaction_id:04d}`
⏰ *THỜI GIAN:* `{current_time}`
{action_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 *SỐ DƯ HIỆN TẠI:* `{group_data['totalAmount']:,}`
💸 *TỔNG PHÍ:* `{group_data['totalFee']:,}`
📊 *PHÍ GIAO DỊCH:* `{fee:,}` ({fee_rate*100:.1f}%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ *GIAO DỊCH ĐÃ ĐƯỢC XỬ LÝ THÀNH CÔNG!* ✅"""
            update.message.reply_text(response, parse_mode='Markdown')
            
        except ValueError:
            update.message.reply_text("⚠️ *Lỗi:* Vui lòng nhập số hợp lệ sau dấu + hoặc -", parse_mode='Markdown')
        except Exception as e:
            update.message.reply_text(f"❌ *Lỗi:* {str(e)}", parse_mode='Markdown')

# Xử lý lệnh /summary
def summary_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Kiểm tra quyền admin
    if user_id not in ADMIN_IDS:
        update.message.reply_text("❌ *Bạn không có quyền sử dụng bot này*", parse_mode='Markdown')
        return
    
    try:
        group_data = get_group_data(chat_id)
        fee_rate = get_fee_rate_for_group(chat_id)
        response = f"""📊 *BÁO CÁO TỔNG KẾT* 📊

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 *TỔNG TIỀN:* `{group_data['totalAmount']:,}`
💸 *TỔNG PHÍ:* `{group_data['totalFee']:,}`
📈 *TỶ LỆ PHÍ:* {fee_rate*100:.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 *SỐ GIAO DỊCH:* {len(group_data.get('transactions', []))}
🕐 *CẬP NHẬT LÚC:* {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        update.message.reply_text(f"❌ *Lỗi khi đọc dữ liệu:* {str(e)}", parse_mode='Markdown')

# Xử lý lệnh /reset_time
def reset_time_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Kiểm tra quyền admin
    if user_id not in ADMIN_IDS:
        update.message.reply_text("❌ *Bạn không có quyền sử dụng bot này*", parse_mode='Markdown')
        return
    
    try:
        now = datetime.now()
        # Tính thời gian đến 00:00 ngày mai
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        seconds_until_midnight = (tomorrow - now).total_seconds()
        
        hours = int(seconds_until_midnight // 3600)
        minutes = int((seconds_until_midnight % 3600) // 60)
        seconds = int(seconds_until_midnight % 60)
        
        response = f"""⏰ *THỜI GIAN RESET TỰ ĐỘNG* ⏰

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 *LẦN RESET TIẾP THEO:* 00:00 ngày mai
⏳ *CÒN LẠI:* {hours:02d}:{minutes:02d}:{seconds:02d}
📅 *NGÀY RESET:* {tomorrow.strftime('%d/%m/%Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 *LƯU Ý:* Dữ liệu sẽ được reset về 0 tự động

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        update.message.reply_text(f"❌ *Lỗi:* {str(e)}", parse_mode='Markdown')

# Tạo keyboard cho admin
def create_admin_keyboard(chat_id=None):
    keyboard = [
        [
            InlineKeyboardButton("📊 Báo cáo", callback_data="summary"),
            InlineKeyboardButton("📋 Lịch sử", callback_data="history")
        ],
        [
            InlineKeyboardButton("🔄 Reset", callback_data="reset"),
            InlineKeyboardButton("⏰ Thời gian", callback_data="reset_time")
        ],
        [
            InlineKeyboardButton("⚙️ Cài đặt", callback_data="settings"),
            InlineKeyboardButton("ℹ️ Hướng dẫn", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Tạo keyboard cho cài đặt
def create_settings_keyboard(chat_id):
    settings = read_settings()
    fee_rate = get_fee_rate_for_group(chat_id)
    
    keyboard = [
        [
            InlineKeyboardButton(f"📊 Phí hiện tại: {fee_rate*100:.1f}%", callback_data="current_fee")
        ],
        [
            InlineKeyboardButton("1%", callback_data="set_fee_0.01"),
            InlineKeyboardButton("2%", callback_data="set_fee_0.02"),
            InlineKeyboardButton("3%", callback_data="set_fee_0.03"),
            InlineKeyboardButton("4%", callback_data="set_fee_0.04")
        ],
        [
            InlineKeyboardButton("5%", callback_data="set_fee_0.05"),
            InlineKeyboardButton("6%", callback_data="set_fee_0.06"),
            InlineKeyboardButton("7%", callback_data="set_fee_0.07"),
            InlineKeyboardButton("8%", callback_data="set_fee_0.08"),
            InlineKeyboardButton("9%", callback_data="set_fee_0.09"),
            InlineKeyboardButton("10%", callback_data="set_fee_0.10")
            InlineKeyboardButton("11%", callback_data="set_fee_0.11")
            InlineKeyboardButton("12%", callback_data="set_fee_0.12")
            InlineKeyboardButton("13%", callback_data="set_fee_0.13"),
            InlineKeyboardButton("15%", callback_data="set_fee_0.15")
        ],
        [
            InlineKeyboardButton("🔙 Quay lại", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Xử lý callback từ nút bấm
def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat.id
    
    try:
        query.answer()
        
        user_id = query.from_user.id
        
        # Kiểm tra quyền admin
        if user_id not in ADMIN_IDS:
            query.edit_message_text("❌ *Bạn không có quyền sử dụng bot này*", parse_mode='Markdown')
            return
        
        print(f"Button pressed: {query.data} by user {user_id} in chat {chat_id}")  # Debug log
        
        if query.data == "summary":
            try:
                group_data = get_group_data(chat_id)
                fee_rate = get_fee_rate_for_group(chat_id)
                response = f"""📊 *BÁO CÁO TỔNG KẾT* 📊

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 *TỔNG TIỀN:* `{group_data['totalAmount']:,}`
💸 *TỔNG PHÍ:* `{group_data['totalFee']:,}`
📈 *TỶ LỆ PHÍ:* {fee_rate*100:.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 *SỐ GIAO DỊCH:* {len(group_data.get('transactions', []))}
🕐 *CẬP NHẬT LÚC:* {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
                try:
                    await query.edit_message_text(response, parse_mode='Markdown', reply_markup=create_admin_keyboard(chat_id))
                except Exception as edit_error:
                    if "Message is not modified" in str(edit_error):
                        await query.answer("📊 Báo cáo tổng kết")
                    else:
                        raise edit_error
            except Exception as e:
                await query.edit_message_text(f"❌ *Lỗi khi đọc dữ liệu:* {str(e)}", parse_mode='Markdown')
        
        elif query.data == "reset":
            # Xác nhận reset
            keyboard = [
                [
                    InlineKeyboardButton("✅ Xác nhận", callback_data="confirm_reset"),
                    InlineKeyboardButton("❌ Hủy", callback_data="back_to_main")
                ]
            ]
            await query.edit_message_text(
                "⚠️ *XÁC NHẬN RESET*\n\nBạn có chắc chắn muốn reset tất cả dữ liệu?",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif query.data == "confirm_reset":
            try:
                group_data = {
                    "totalAmount": 0,
                    "totalFee": 0,
                    "transactions": [],
                    "transactionCount": 0
                }
                update_group_data(chat_id, group_data)
                
                try:
                    await query.edit_message_text(
                        "✅ *ĐÃ RESET THÀNH CÔNG*\n\nTất cả dữ liệu đã được reset về 0.",
                        parse_mode='Markdown',
                        reply_markup=create_admin_keyboard(chat_id)
                    )
                except Exception as edit_error:
                    if "Message is not modified" in str(edit_error):
                        await query.answer("✅ Đã reset thành công")
                    else:
                        raise edit_error
            except Exception as e:
                await query.edit_message_text(f"❌ *Lỗi khi reset:* {str(e)}", parse_mode='Markdown')
        
        elif query.data == "history":
            try:
                group_data = get_group_data(chat_id)
                transactions = group_data.get("transactions", [])
                
                if not transactions:
                    response = "📋 *LỊCH SỬ GIAO DỊCH*\n\nChưa có giao dịch nào."
                else:
                    # Hiển thị 10 giao dịch gần nhất
                    recent_transactions = transactions[-10:]
                    response = "📋 *LỊCH SỬ GIAO DỊCH*\n\n"
                    
                    for tx in reversed(recent_transactions):
                        # Xác định icon và format cho số tiền
                        if tx['amount'] > 0:
                            amount_icon = "💚"
                            amount_text = f"+{tx['amount']:,}"
                        else:
                            amount_icon = "🔴"
                            amount_text = f"{tx['amount']:,}"
                        
                        response += f"🆔 `#{tx['id']:04d}` | ⏰ `{tx['timestamp']}`\n"
                        response += f"{amount_icon} `{amount_text}` | 💸 `{tx['fee']:,}` ({tx['fee_rate']*100:.1f}%)\n"
                        response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    
                    response += f"\n📊 **Tổng:** {len(transactions)} giao dịch"
                
                try:
                    await query.edit_message_text(response, parse_mode='Markdown', reply_markup=create_admin_keyboard(chat_id))
                except Exception as edit_error:
                    if "Message is not modified" in str(edit_error):
                        await query.answer("📋 Lịch sử giao dịch")
                    else:
                        raise edit_error
            except Exception as e:
                await query.edit_message_text(f"❌ *Lỗi khi đọc lịch sử:* {str(e)}", parse_mode='Markdown')
        
        elif query.data == "reset_time":
             try:
                 now = datetime.now()
                 # Tính thời gian đến 00:00 ngày mai
                 tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                 seconds_until_midnight = (tomorrow - now).total_seconds()
                 
                 hours = int(seconds_until_midnight // 3600)
                 minutes = int((seconds_until_midnight % 3600) // 60)
                 seconds = int(seconds_until_midnight % 60)
                 
                 response = f"""⏰ *THỜI GIAN RESET TỰ ĐỘNG* ⏰

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 *LẦN RESET TIẾP THEO:* 00:00 ngày mai
⏳ *CÒN LẠI:* {hours:02d}:{minutes:02d}:{seconds:02d}
📅 *NGÀY RESET:* {tomorrow.strftime('%d/%m/%Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 *LƯU Ý:* Dữ liệu sẽ được reset về 0 tự động

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
                 
                 try:
                     await query.edit_message_text(response, parse_mode='Markdown', reply_markup=create_admin_keyboard(chat_id))
                 except Exception as edit_error:
                     if "Message is not modified" in str(edit_error):
                         await query.answer("⏰ Thời gian reset")
                     else:
                         raise edit_error
             except Exception as e:
                 await query.edit_message_text(f"❌ *Lỗi:* {str(e)}", parse_mode='Markdown')
        
        elif query.data == "settings":
            try:
                fee_rate = get_fee_rate_for_group(chat_id)
                response = f"""⚙️ *CÀI ĐẶT PHÍ GIAO DỊCH* ⚙️

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 *PHÍ HIỆN TẠI:* {fee_rate*100:.1f}%

Chọn mức phí mới cho nhóm này:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
                await query.edit_message_text(response, parse_mode='Markdown', reply_markup=create_settings_keyboard(chat_id))
            except Exception as e:
                await query.edit_message_text(f"❌ *Lỗi:* {str(e)}", parse_mode='Markdown')
        
        elif query.data.startswith("set_fee_"):
            try:
                new_fee_rate = float(query.data.replace("set_fee_", ""))
                settings = read_settings()
                
                # Cập nhật cài đặt cho nhóm này
                settings["group_settings"][str(chat_id)] = {
                    "fee_rate": new_fee_rate,
                    "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }
                save_settings(settings)
                
                response = f"""✅ *ĐÃ CẬP NHẬT PHÍ THÀNH CÔNG* ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 *PHÍ MỚI:* {new_fee_rate*100:.1f}%
⏰ *CẬP NHẬT LÚC:* {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ *CÀI ĐẶT ĐÃ ĐƯỢC LƯU THÀNH CÔNG!* ✅"""
                await query.edit_message_text(response, parse_mode='Markdown', reply_markup=create_admin_keyboard(chat_id))
            except Exception as e:
                await query.edit_message_text(f"❌ *Lỗi khi cập nhật phí:* {str(e)}", parse_mode='Markdown')
        
        elif query.data == "current_fee":
            try:
                fee_rate = get_fee_rate_for_group(chat_id)
                settings = read_settings()
                group_settings = settings["group_settings"].get(str(chat_id), {})
                
                if str(chat_id) in settings["group_settings"]:
                    updated_at = group_settings.get("updated_at", "Không xác định")
                    response = f"""📊 *THÔNG TIN PHÍ HIỆN TẠI* 📊

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💸 *MỨC PHÍ:* {fee_rate*100:.1f}%
⏰ *CẬP NHẬT LÚC:* {updated_at}
📍 *LOẠI:* Phí riêng cho nhóm này

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
                else:
                    response = f"""📊 *THÔNG TIN PHÍ HIỆN TẠI* 📊

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💸 *MỨC PHÍ:* {fee_rate*100:.1f}%
📍 *LOẠI:* Phí mặc định toàn hệ thống

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
                
                await query.edit_message_text(response, parse_mode='Markdown', reply_markup=create_settings_keyboard(chat_id))
            except Exception as e:
                await query.edit_message_text(f"❌ *Lỗi:* {str(e)}", parse_mode='Markdown')
          
        elif query.data == "help":
            help_text = """🤖 *HƯỚNG DẪN SỬ DỤNG* 🤖

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 *CÁCH SỬ DỤNG:*

➕ *CỘNG TIỀN:* Gửi tin nhắn bắt đầu bằng "+" 
   Ví dụ: `+1000`, `+50000`
➖ *TRỪ TIỀN:* Gửi tin nhắn bắt đầu bằng "-"
   Ví dụ: `-1000`, `-50000`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 *XEM BÁO CÁO:* Xem tổng tiền và phí hiện tại
📋 *LỊCH SỬ GIAO DỊCH:* Xem 10 giao dịch gần nhất
🔄 *RESET DỮ LIỆU:* Xóa tất cả dữ liệu về 0
⏰ *THỜI GIAN RESET:* Xem thời gian reset tự động
⚙️ *CÀI ĐẶT PHÍ:* Thay đổi mức phí cho nhóm này

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 *LƯU Ý:* 
• Phí giao dịch có thể được cài đặt riêng cho từng nhóm
• Không thể trừ tiền nhiều hơn số tiền hiện có
• Dữ liệu sẽ tự động reset về 0 lúc 00:00 hàng ngày
• Mỗi nhóm có dữ liệu và cài đặt riêng biệt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
            try:
                await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=create_admin_keyboard(chat_id))
            except Exception as edit_error:
                if "Message is not modified" in str(edit_error):
                    await query.answer("ℹ️ Hướng dẫn sử dụng")
                else:
                    raise edit_error
        
        elif query.data == "back_to_main":
            try:
                await query.edit_message_text(
                    "🤖 *BOT QUẢN LÝ TIỀN*\n\nChọn chức năng bạn muốn sử dụng:",
                    parse_mode='Markdown',
                    reply_markup=create_admin_keyboard(chat_id)
                )
            except Exception as edit_error:
                if "Message is not modified" in str(edit_error):
                    await query.answer("🔙 Quay lại menu chính")
                else:
                    raise edit_error
                
    except Exception as e:
        print(f"Critical error in button callback: {str(e)}")  # Debug log

# Hàm khởi tạo bot
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Kiểm tra quyền admin
    if user_id not in ADMIN_IDS:
        update.message.reply_text("❌ *Bạn không có quyền sử dụng bot này*", parse_mode='Markdown')
        return
    
    print(f"Start command received from user {user_id} in chat {chat_id}")  # Debug log
    
    welcome_message = """🤖 *BOT QUẢN LÝ TIỀN CHUYÊN NGHIỆP* 🤖

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Chào mừng bạn đến với hệ thống quản lý tiền tự động!

💡 *CÁCH SỬ DỤNG:*
• Nhập `+1000` để cộng tiền
• Nhập `-500` để trừ tiền  
• Gõ `/start` để hiển thị menu

Chọn chức năng bạn muốn sử dụng:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=create_admin_keyboard(chat_id))

# Hàm chính
def main():
    global bot_application
    
    # Khởi tạo các file cần thiết
    init_total_file()
    init_settings_file()
    
    # Tạo updater bot
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    bot_application = updater  # Lưu để auto reset có thể sử dụng
    
    # Thêm các handler
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("summary", summary_command))
    dispatcher.add_handler(CommandHandler("test", lambda u, c: u.message.reply_text("✅ Bot đang hoạt động!")))
    dispatcher.add_handler(CommandHandler("reset_time", reset_time_command))
    dispatcher.add_handler(CallbackQueryHandler(button_callback))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Khởi động bot và auto reset
    print("🤖 Bot đang chạy...")
    print("🔄 Auto reset sẽ chạy lúc 00:00 hàng ngày")
    print("⚙️ Hỗ trợ cài đặt phí riêng cho từng nhóm")
    print("🎨 Giao diện đã được cải tiến chuyên nghiệp")
    
    # Chạy auto reset trong thread riêng
    auto_reset_thread = threading.Thread(target=auto_reset_daily, daemon=True)
    auto_reset_thread.start()
    
    # Chạy bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
