import asyncio
import logging
import time
import os
import threading
import requests
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PIXEL_ID = "2548037185690331"
CAPI_TOKEN = "EAAZA8siXlGj4BTHCuThnWMuL0uJZBPZCviAZAI6HuLdDJQo46qevFfEpVwywqbFe2cvAkYZAvvBjFLvJwRHHQdweKw6r86bGgWe9rcRbYQpiLez0SPS3ainjb9dFGzSlcHxLXVcZADK0FzAFPZA1nfTDPwcWIcOfZBZBcOoeZBAYuT5WEAMPL3FkSLjNZBMvI8usgPCgQZDZD"
CHANNEL_ID = -1004451542132
CHANNEL_LINK = "https://letsmon.xyz/ujap9ewvblrw"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def send_subscribe_event(user_id: int):
    url = f"https://graph.facebook.com/v19.0/{PIXEL_ID}/events"
    payload = {
        "data": [{
            "event_name": "Subscribe",
            "event_time": int(time.time()),
            "action_source": "website",
            "user_data": {"external_id": str(user_id)}
        }],
        "access_token": CAPI_TOKEN
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        logging.info(f"CAPI response: {r.status_code} {r.text}")
    except Exception as e:
        logging.error(f"CAPI error: {e}")

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        logging.error(f"check_subscription error: {e}")
        return False

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    if await check_subscription(user_id):
        send_subscribe_event(user_id)
        await message.answer("Спасибо! Вы подписаны на канал ✅\n" f"Перейти в канал: {CHANNEL_LINK}")
    else:
        await message.answer("Привет! Чтобы продолжить, подпишитесь на наш канал:\n" f"{CHANNEL_LINK}\n\n" "После подписки нажмите /start ещё раз.")

# --- Веб-сервер для Render (чтобы не засыпал) ---
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running", 200

def run_bot():
    # Запускаем Long Polling в отдельном потоке
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(dp.start_polling(bot))

if __name__ == "__main__":
    # Запускаем бота в фоне
    threading.Thread(target=run_bot, daemon=True).start()
    # Запускаем Flask для Render
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)