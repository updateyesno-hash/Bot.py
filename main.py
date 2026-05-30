import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")

# ВАЖНО: Базовый URL для нового API
BASE_URL = "https://api.greedy-sms.com"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Универсальная функция для запросов к новому API
def send_api_request(method, endpoint, data=None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}" # Авторизация из доков
    }
    url = f"{BASE_URL}/{endpoint}"
    # Используем POST для всех методов, как на скринах
    resp = requests.post(url, json=data or {}, headers=headers)
    return resp.json()

@dp.message(Command("start"))
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить номер TG", callback_data="buy_tg")],
        [InlineKeyboardButton(text="🌍 Список стран", callback_data="list_countries")]
    ])
    await message.answer("Бот готов. Выберите действие:", reply_markup=kb)

@dp.callback_query(F.data == "list_countries")
async def show_countries(callback: CallbackQuery):
    # Согласно документации на скрине 1000086861.jpg
    # POST /activations/getCountries требует body: {"page": 1, "pageSize": 50}
    data = {"page": 1, "pageSize": 50}
    result = send_api_request("POST", "activations/getCountries", data)
    
    if "countries" in result:
        text = "Доступные страны (ID: Название):\n"
        for c in result["countries"]:
            text += f"{c['id']} : {c['title']['rus']}\n"
        await callback.message.answer(text[:4096])
    else:
        await callback.message.answer(f"Ошибка получения стран: {result}")
    await callback.answer()

@dp.callback_query(F.data == "buy_tg")
async def buy_number(callback: CallbackQuery):
    # Пример для покупки. ID страны должен быть верным (например 1)
    # ID сервиса для TG обычно 'tg'
    data = {"service": "tg", "country": 1}
    result = send_api_request("POST", "activations/getNumber", data)
    
    if "activationId" in result:
        await callback.message.answer(f"✅ Номер получен: {result['phone']}\nID: {result['activationId']}")
    else:
        await callback.message.answer(f"❌ Ошибка: {result}")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
