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
@bot.message_handler(commands=['spx'])
def check_spx(message):
    if message.from_user.id != ID_CUA_BAN: return
    mvd = message.text.replace('/spx', '').strip()
    if not mvd: return bot.reply_to(message, "⚠️ Nhập mã vận đơn sếp ơi!")
    bot.reply_to(message, f"⏳ Đang tra hành trình {mvd}...")
    try:
        url = f"https://spx.vn/api/v2/fleet_order/tracking/search?sls_tracking_number={mvd}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()
        if res.get('message') == 'success' and res.get('data') and res['data'].get('tracking_info'):
            tracking_info = res['data']['tracking_info']
            text_reply = f"📦 <b>MÃ VẬN ĐƠN: {mvd}</b>\n\n"
            for track in tracking_info:
                try:
                    ts = int(track.get('timestamp', track.get('update_time', 0)))
                    thoi_gian = datetime.datetime.fromtimestamp(ts).strftime('%H:%M - %d/%m/%Y')
                except: thoi_gian = str(track.get('timestamp', ''))
                mo_ta = track.get('description', '')
                text_reply += f"🕒 <b>{thoi_gian}</b>\n📍 {mo_ta}\n〰️〰️〰️〰️〰️\n"
            if len(text_reply) > 4000: bot.send_message(message.chat.id, text_reply[:4000] + "\n...(Cắt bớt)", parse_mode='HTML')
            else: bot.send_message(message.chat.id, text_reply, parse_mode='HTML')
        else: bot.reply_to(message, "❌ Không tìm thấy cục hàng này trên hệ thống.")
    except Exception as e: bot.reply_to(message, f"❌ Lỗi mạng: {e}")

# --- CỔNG WEB ẢO CHO RENDER ---
@app.route('/')
def ping():
    return "Bot Trinh Sát đang sống nhăn răng!", 200

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # Tách bot ra chạy luồng riêng để không bị đụng với Flask
    t = threading.Thread(target=run_bot)
    t.start()
    # Chạy Web ảo để Render kích hoạt
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)