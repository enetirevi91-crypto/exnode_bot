import asyncio
import logging
import time
import os
import threading
import requests
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PIXEL_ID = "4710337062579164" 
CAPI_TOKEN = "EAAZAidD25ajgBTNxa9oZCmPmLEIo1ZC13vwH3gCHzyFXQaErgpHaHznUro82HOLsicoOnL03SH347oEZBZAaQ9RzZAaUeb1xWroWLGkiG3xawJVmOuZCrpBa7bHiIE6ANj5lojbBoniG2usJSUUYv6qVPffTZBweZBLyNbXT8Bp8x5dvn8IJysh9NjlwB4X9wRZCjL8wZDZD"
CHANNEL_ID = -1004451542132
CHANNEL_LINK = "https://letsmon.xyz/ujap9ewvblrw"
MANAGER_LINK = "https://t.me/Manager_Exnode"

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

def get_subscribe_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на канал", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")]
    ])
    return keyboard

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    subscribed = await check_subscription(user_id)
    
    if subscribed:
        send_subscribe_event(user_id)
        
        # Если уже подписан, тоже даем кнопки менеджера и канала
        success_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Перейти в канал", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="👨‍💻 Написать менеджеру", url=MANAGER_LINK)]
        ])
        
        await message.answer(
            "Отлично! Вы уже подписаны ✅\n"
            "Теперь вы можете перейти в канал или связаться с менеджером.",
            reply_markup=success_keyboard
        )
    else:
        await message.answer(
            "Привет! Чтобы продолжить, подпишись на наш канал 👇",
            reply_markup=get_subscribe_keyboard()
        )

@dp.callback_query(F.data == "check_sub")
async def callback_check_sub(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    subscribed = await check_subscription(user_id)
    
    if subscribed:
        send_subscribe_event(user_id)
        
        # Кнопки после успешной подписки
        success_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Перейти в канал", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="👨‍💻 Написать менеджеру", url=MANAGER_LINK)]
        ])
        
        await callback.message.edit_text(
            "Спасибо! Вы подписаны ✅\n"
            "Теперь вы можете перейти в канал или связаться с менеджером.",
            reply_markup=success_keyboard
        )
    else:
        await callback.answer(
            "Вы еще не подписались на канал! Пожалуйста, подпишитесь и нажмите кнопку снова.",
            show_alert=True
        )

# --- Веб-сервер для Render (работает в фоне) ---
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

if __name__ == "__main__":
    # Flask в фоне для Render
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Бот в главном потоке (чтобы не было ошибки set_wakeup_fd)
    logging.info("Starting bot polling in main thread...")
    dp.run_polling(bot)