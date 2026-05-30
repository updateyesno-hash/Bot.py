import asyncio
import os
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

# Настройки
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.greedy-sms.com/stubs/handler_api.php"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРА ---
def get_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить номер TG", callback_data="buy_tg")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="profile")]
    ])

# --- ЛОГИКА ---
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=get_main_kb())

@dp.callback_query(F.data == "profile")
async def check_balance(callback: CallbackQuery):
    params = {"api_key": API_KEY, "action": "getBalance"}
    resp = requests.get(BASE_URL, params=params).text
    await callback.message.answer(f"Ваш баланс: {resp.split(':')[1] if ':' in resp else resp} руб.")
    await callback.answer()

@dp.callback_query(F.data == "buy_tg")
async def buy_number(callback: CallbackQuery):
    await callback.message.answer("Запрашиваю номер...")
    
    # 1. Заказ номера
    params = {"api_key": API_KEY, "action": "getNumber", "service": "tg"}
    resp = requests.get(BASE_URL, params=params).text
    
    if not resp.startswith("ACCESS_NUMBER"):
        await callback.message.answer(f"Ошибка получения номера: {resp}")
        return

    _, order_id, phone = resp.split(":")
    await callback.message.answer(f"✅ Номер: +{phone}\nЖду СМС (таймаут 3 мин)...")

    # 2. Ожидание СМС (цикл на 36 итераций по 5 секунд)
    for i in range(36):
        await asyncio.sleep(5)
        status_params = {"api_key": API_KEY, "action": "getStatus", "id": order_id}
        status_resp = requests.get(BASE_URL, params=status_params).text
        
        if status_resp.startswith("STATUS_OK"):
            code = status_resp.split(":")[1]
            await callback.message.answer(f"🎉 Код успешно получен: {code}")
            return
        
    await callback.message.answer("⏱ Время ожидания вышло. Номер был отменен.")
    requests.get(BASE_URL, params={"api_key": API_KEY, "action": "setStatus", "id": order_id, "status": 8})

# --- ЗАПУСК ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот запущен и готов к работе.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
