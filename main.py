import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")

# Используем тот же URL, что был в самом начале, но с правильным методом
BASE_URL = "https://api.greedy-sms.com/stubs/handler_api.php"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Функция отправки запроса через параметры
def send_legacy_request(action, params=None):
    if params is None:
        params = {}
    params["api_key"] = API_KEY
    params["action"] = action
    
    response = requests.get(BASE_URL, params=params)
    return response.text

@dp.message(Command("start"))
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить номер TG", callback_data="buy_tg")],
        [InlineKeyboardButton(text="🌍 Список стран", callback_data="list_countries")]
    ])
    await message.answer("Бот запущен (Legacy API mode):", reply_markup=kb)

@dp.callback_query(F.data == "list_countries")
async def show_countries(callback: CallbackQuery):
    resp = send_legacy_request("getCountries")
    await callback.message.answer(f"Ответ от сервера:\n{resp}")
    await callback.answer()

@dp.callback_query(F.data == "buy_tg")
async def buy_number(callback: CallbackQuery):
    # country=1 (Россия), service='tg'
    resp = send_legacy_request("getNumber", {"service": "tg", "country": 1})
    await callback.message.answer(f"Ответ от сервера:\n{resp}")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
