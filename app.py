import telebot
import requests
import re
import urllib.parse
import datetime
from flask import Flask
import threading
import os

TOKEN = "8794870921:AAHPbiy4UwwoAJJi-swNQPQz2CJpcFeBysk"
ID_CUA_BAN = 6316013638

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- Lệnh /start cho vui cửa vui nhà ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "🚀 Bot Trinh Sát 24/24 đã sẵn sàng nhận lệnh từ sếp!")

# --- Lệnh /danhmuc ---
@bot.message_handler(commands=['danhmuc'])
def check_danh_muc(message):
    if message.from_user.id != ID_CUA_BAN: return
    link = message.text.replace('/danhmuc', '').strip()
    if not link: return bot.reply_to(message, "⚠️ Nhập link Shopee sếp ơi!")
    bot.reply_to(message, "⏳ Đang soi danh mục, đợi xíu...")
    try:
        if "shp.ee" in link or "shope.ee" in link:
            r = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5, allow_redirects=True)
            link = r.url
        match = re.search(r'i\.(\d+)\.(\d+)', link) or re.search(r'product/(\d+)/(\d+)', link)
        if not match: return bot.reply_to(message, "❌ Không nhận diện được ID SP!")
        shop_id, item_id = match.groups()
        api_url = f"https://shopee.vn/api/v4/item/get?itemid={item_id}&shopid={shop_id}"
        res = requests.get(api_url, headers={'User-Agent': 'Mozilla/5.0'}).json()
        if 'data' in res and res['data'] and 'categories' in res['data']:
            categories = res['data']['categories']
            ten_sp = res['data'].get('name', 'Sản phẩm')
            chuoi_dm = " > ".join([c['display_name'] for c in categories])
            bot.reply_to(message, f"📦 <b>{ten_sp}</b>\n\n🏷️ <b>Ngành hàng:</b>\nShopee > {chuoi_dm}", parse_mode='HTML')
        else: bot.reply_to(message, "❌ Shopee chặn lấy dữ liệu hoặc SP không tồn tại.")
    except Exception as e: bot.reply_to(message, f"❌ Lỗi mạng: {e}")

# --- Lệnh /spx ---
# --- Lệnh /spx (Gửi kết quả thẳng về chat, vượt rào bảo mật) ---
@bot.message_handler(commands=['spx'])
def check_spx(message):
    if message.from_user.id != ID_CUA_BAN: return
    mvd = message.text.replace('/spx', '').strip()
    if not mvd: return bot.reply_to(message, "⚠️ Nhập mã vận đơn sếp ơi!\nVD: <code>/spx SPXVN123456</code>", parse_mode='HTML')
    
    bot.reply_to(message, f"⏳ Đang bóc tách dữ liệu hành trình {mvd}...")
    try:
        # Giả lập bộ Header đầy đủ thông tin của một trình duyệt thật đang lướt SPX
        url = f"https://spx.vn/api/v2/fleet_order/tracking/search?sls_tracking_number={mvd}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://spx.vn/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        res = response.json()
        
        if res.get('message') == 'success' and res.get('data') and res.get('data').get('tracking_info'):
            tracking_info = res['data']['tracking_info']
            text_reply = f"📦 <b>HÀNH TRÌNH MÃ VẬN ĐƠN:</b> <code>{mvd}</code>\n\n"
            
            for track in tracking_info:
                try:
                    ts = int(track.get('timestamp', track.get('update_time', 0)))
                    thoi_gian = datetime.datetime.fromtimestamp(ts).strftime('%H:%M - %d/%m/%Y')
                except: 
                    thoi_gian = str(track.get('timestamp', track.get('update_time', '')))
                
                mo_ta = track.get('description', '')
                text_reply += f"🕒 <b>{thoi_gian}</b>\n📍 {mo_ta}\n〰️〰️〰️〰️〰️\n"
            
            if len(text_reply) > 4000:
                bot.send_message(message.chat.id, text_reply[:4000] + "\n...(Đã cắt bớt vì quá dài)", parse_mode='HTML')
            else:
                bot.send_message(message.chat.id, text_reply, parse_mode='HTML')
        else:
            bot.reply_to(message, f"❌ Không tìm thấy thông tin. (Mã hoặc đơn đã cũ / không tồn tại trên hệ thống SPX).")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Lỗi kết nối tới máy chủ SPX: {e}")

# --- Lệnh /spx (Tra cứu nhanh, chống lỗi chặn API từ SPX) ---
@bot.message_handler(commands=['spx'])
def check_spx(message):
    if message.from_user.id != ID_CUA_BAN: return
    mvd = message.text.replace('/spx', '').strip()
    if not mvd: return bot.reply_to(message, "⚠️ Nhập mã vận đơn sếp ơi!\nVD: <code>/spx SPXVN123456</code>", parse_mode='HTML')
    
    # Tạo nút bấm điều hướng thẳng tới trang tra cứu chính thức của SPX
    bang_nut = InlineKeyboardMarkup()
    link_tra_cuu = f"https://spx.vn/tracking?logistic_tracking_number={mvd}"
    nut_bam = InlineKeyboardButton("🔍 Xem Full Hành Trình Tại SPX", url=link_tra_cuu)
    bang_nut.add(nut_bam)
    
    bot.reply_to(
        message, 
        f"📦 <b>MÃ VẬN ĐƠN:</b> <code>{mvd}</code>\n\n⚡ SPX chặn API server ngoài nên bot tạo sẵn lối tắt chính hãng cho sếp:", 
        reply_markup=bang_nut, 
        parse_mode='HTML'
    )
# --- CỔNG WEB ẢO CHO RENDER ---
@app.route('/')
def ping():
    return "Bot Trinh Sát đang sống nhăn răng!", 200

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
