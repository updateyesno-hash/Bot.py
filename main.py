import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.greedy-sms.com"

bot = Bot(token=TOKEN)
dp = Dispatcher()

def send_api_request(endpoint, data=None):
    # Добавляем ключ в само тело запроса, а не в заголовки
    if data is None:
        data = {}
    data["apiKey"] = API_KEY  # ВОТ ЗДЕСЬ ИЗМЕНЕНИЕ
    
    headers = {"Content-Type": "application/json"}
    url = f"{BASE_URL}/{endpoint}"
    
    response = requests.post(url, json=data, headers=headers)
    return response.status_code, response.json()

@dp.message(Command("start"))
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить номер TG", callback_data="buy_tg")],
        [InlineKeyboardButton(text="🌍 Список стран", callback_data="list_countries")]
    ])
    await message.answer("Бот готов. Используем apiKey в теле запроса:", reply_markup=kb)

@dp.callback_query(F.data == "list_countries")
async def show_countries(callback: CallbackQuery):
    status, result = send_api_request("activations/getCountries", {"page": 1, "pageSize": 50})
    if status == 200 and "countries" in result:
        text = "Доступные страны:\n"
        for c in result["countries"]:
            text += f"{c['id']} : {c['title']['rus']}\n"
        await callback.message.answer(text[:4096])
    else:
        await callback.message.answer(f"Ошибка {status}: {result}")
    await callback.answer()

@dp.callback_query(F.data == "buy_tg")
async def buy_number(callback: CallbackQuery):
    # country=1 (Россия), service='tg'
    status, result = send_api_request("activations/getNumber", {"service": "tg", "country": 1})
    if status == 200 and "activationId" in result:
        await callback.message.answer(f"✅ Номер: {result['phone']}\nID: {result['activationId']}")
    else:
        await callback.message.answer(f"❌ Ошибка {status}: {result}")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
