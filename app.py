import telebot
import re
from flask import Flask
import threading
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

TOKEN = "8794870921:AAHPbiy4UwwoAJJi-swNQPQz2CJpcFeBysk"
ID_CUA_BAN = 6316013638

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- Lệnh /start ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "🚀 Bot Trinh Sát 24/24 đã lên sóng, sẵn sàng nhận lệnh!")

# --- Lệnh /danhmuc ---
@bot.message_handler(commands=['danhmuc'])
def check_danh_muc(message):
    if message.from_user.id != ID_CUA_BAN: return
    link = message.text.replace('/danhmuc', '').strip()
    if not link: return bot.reply_to(message, "⚠️ Nhập link Shopee sếp ơi!")
    
    bot.reply_to(message, "⏳ Đang soi danh mục, đợi xíu...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        if "shp.ee" in link or "shope.ee" in link:
            r = requests.get(link, headers=headers, timeout=5, allow_redirects=True)
            link = r.url
            
        match = re.search(r'i\.(\d+)\.(\d+)', link) or re.search(r'product/(\d+)/(\d+)', link)
        if not match: return bot.reply_to(message, "❌ Không nhận diện được ID SP!")
        shop_id, item_id = match.groups()
        
        res = requests.get(f"https://shopee.vn/api/v4/item/get?itemid={item_id}&shopid={shop_id}", headers=headers).json()
        if 'data' in res and res['data'] and 'categories' in res['data']:
            chuoi_dm = " > ".join([c['display_name'] for c in res['data']['categories']])
            bot.reply_to(message, f"📦 <b>{res['data'].get('name', 'Sản phẩm')}</b>\n\n🏷️ <b>Ngành hàng:</b>\nShopee > {chuoi_dm}", parse_mode='HTML')
        else: 
            bot.reply_to(message, "❌ Shopee chặn lấy dữ liệu API.")
    except Exception as e: bot.reply_to(message, f"❌ Lỗi mạng: {e}")

# --- Lệnh /spx (Tra cứu bằng Nút Bấm Chống Chặn) ---
@bot.message_handler(commands=['spx'])
def check_spx(message):
    if message.from_user.id != ID_CUA_BAN: return
    mvd = message.text.replace('/spx', '').strip()
    
    if not mvd: 
        return bot.reply_to(message, "⚠️ Nhập mã vận đơn vô sếp ơi!\nVD: <code>/spx SPXVN123456</code>", parse_mode='HTML')
    
    bang_nut = InlineKeyboardMarkup()
    link_tra_cuu = f"https://spx.vn/tracking?logistic_tracking_number={mvd}"
    bang_nut.add(InlineKeyboardButton("🚀 MỞ TRANG TRA CỨU SPX", url=link_tra_cuu))
    
    bot.reply_to(
        message, 
        f"📦 <b>MÃ VẬN ĐƠN:</b> <code>{mvd}</code>\n\n⚡ SPX đang khóa IP máy chủ đám mây. Sếp bấm nút dưới đây để xem full hành trình chính gốc nhé:", 
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
