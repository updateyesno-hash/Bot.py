import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")

# Основной URL API
BASE_URL = "https://api.greedy-sms.com"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Функция отправки запросов
def send_api_request(endpoint, data=None):
    # ОЧЕНЬ ВАЖНО: 
    # В документации на скринах указан способ передачи API ключа.
    # Если Bearer не работает, попробуйте изменить ключ в заголовке на 'X-API-KEY'
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}" 
    }
    url = f"{BASE_URL}/{endpoint}"
    
    # Отправляем POST запрос с JSON-телом
    response = requests.post(url, json=data or {}, headers=headers)
    
    # Возвращаем статус и данные для отладки
    return response.status_code, response.json()

@dp.message(Command("start"))
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить номер TG", callback_data="buy_tg")],
        [InlineKeyboardButton(text="🌍 Список стран", callback_data="list_countries")]
    ])
    await message.answer("Бот готов к работе через REST API:", reply_markup=kb)

@dp.callback_query(F.data == "list_countries")
async def show_countries(callback: CallbackQuery):
    status, result = send_api_request("activations/getCountries", {"page": 1, "pageSize": 50})
    
    if status == 200 and "countries" in result:
        text = "Доступные страны:\n"
        for c in result["countries"]:
            text += f"{c['id']} : {c['title']['rus']}\n"
        await callback.message.answer(text[:4096])
    else:
        # Теперь мы увидим реальную ошибку, если статус не 200
        await callback.message.answer(f"Ошибка (код {status}): {result}")
    await callback.answer()

@dp.callback_query(F.data == "buy_tg")
async def buy_number(callback: CallbackQuery):
    # Для покупки используем id страны (например, 1)
    data = {"service": "tg", "country": 1}
    status, result = send_api_request("activations/getNumber", data)
    
    if status == 200 and "activationId" in result:
        await callback.message.answer(f"✅ Номер получен: {result['phone']}\nID: {result['activationId']}")
    else:
        await callback.message.answer(f"❌ Ошибка (код {status}): {result}")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
