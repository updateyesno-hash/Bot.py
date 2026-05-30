import asyncio
import os
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

# Настройки (Берем из Variables в Railway!)
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.greedy-sms.com/stubs/handler_api.php"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРА ---
def get_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить номер TG", callback_data="buy_tg")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="profile")],
        [InlineKeyboardButton(text="🌍 Список стран", callback_data="list_countries")]
    ])

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Магазин готов! Выбери действие:", reply_markup=get_main_kb())

@dp.callback_query(F.data == "profile")
async def check_balance(callback: CallbackQuery):
    params = {"api_key": API_KEY, "action": "getBalance"}
    resp = requests.get(BASE_URL, params=params).text
    await callback.message.answer(f"💰 Ваш баланс: {resp.split(':')[1] if ':' in resp else resp} руб.")
    await callback.answer()

@dp.callback_query(F.data == "list_countries")
async def show_countries(callback: CallbackQuery):
    params = {"api_key": API_KEY, "action": "getCountries"}
    resp = requests.get(BASE_URL, params=params).text
    await callback.message.answer(f"Коды стран (ID:Название):\n{resp}")
    await callback.answer()

@dp.callback_query(F.data == "buy_tg")
async def buy_number(callback: CallbackQuery):
    # Укажи ID страны, который узнаешь через /countries (например, 1 - Россия)
    country_id = "1" 
    
    await callback.message.answer(f"⏳ Запрашиваю номер для TG (Страна ID: {country_id})...")
    
    params = {"api_key": API_KEY, "action": "getNumber", "service": "tg", "country": country_id}
    resp = requests.get(BASE_URL, params=params).text
    
    if resp == "NO_NUMBERS":
        await callback.message.answer("❌ Номеров нет. Попробуйте сменить страну.")
    elif resp == "NO_BALANCE":
        await callback.message.answer("❌ Недостаточно средств.")
    elif resp.startswith("ACCESS_NUMBER"):
        _, order_id, phone = resp.split(":")
        await callback.message.answer(f"✅ Номер: +{phone}\nID заказа: {order_id}\nЖду СМС...")

        # Цикл ожидания СМС (3 минуты)
        for i in range(36):
            await asyncio.sleep(5)
            status_params = {"api_key": API_KEY, "action": "getStatus", "id": order_id}
            status_resp = requests.get(BASE_URL, params=status_params).text
            
            if status_resp.startswith("STATUS_OK"):
                code = status_resp.split(":")[1]
                await callback.message.answer(f"🎉 Код успешно получен: {code}")
                return
        
        await callback.message.answer("⏱ Время вышло. Заказ отменен.")
        requests.get(BASE_URL, params={"api_key": API_KEY, "action": "setStatus", "id": order_id, "status": 8})
    else:
        await callback.message.answer(f"Ошибка: {resp}")
    await callback.answer()

# --- ЗАПУСК ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
