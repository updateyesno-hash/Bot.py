import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Настройки из Railway
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
# Базовый URL для нового API
BASE_URL = "https://api.greedy-sms.com/activations"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Функция для POST-запросов к API
def send_api_request(endpoint, data=None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}" # Авторизация через Bearer
    }
    url = f"{BASE_URL}/{endpoint}"
    response = requests.post(url, json=data or {}, headers=headers)
    return response.json()

# Клавиатура
def get_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить номер TG", callback_data="buy_tg")],
        [InlineKeyboardButton(text="🌍 Список стран", callback_data="list_countries")]
    ])

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Бот готов к работе через GreedySMS API:", reply_markup=get_kb())

@dp.callback_query(F.data == "list_countries")
async def show_countries(callback: CallbackQuery):
    # Запрашиваем страны (page 1)
    result = send_api_request("getCountries", {"page": 1, "pageSize": 20})
    text = "Доступные страны (ID:Название):\n"
    for c in result.get("countries", []):
        text += f"{c['id']} : {c['title']['rus']}\n"
    await callback.message.answer(text[:4096])
    await callback.answer()

@dp.callback_query(F.data == "buy_tg")
async def buy_number(callback: CallbackQuery):
    # country=1 (Россия). Если нужно другое - измени ID
    data = {"service": "tg", "country": 1}
    result = send_api_request("getNumber", data)
    
    if "activationId" in result:
        act_id = result['activationId']
        await callback.message.answer(f"✅ Номер: {result['phone']}\nID: {act_id}\nЖду СМС...")
        
        # Цикл проверки статуса
        for _ in range(20):
            await asyncio.sleep(10)
            status_res = send_api_request("getStatus", {"activationId": act_id})
            if status_res.get("status") == "STATUS_OK":
                await callback.message.answer(f"🎉 СМС получено: {status_res.get('sms')}")
                return
        await callback.message.answer("⏱ Время ожидания истекло.")
    else:
        await callback.message.answer(f"❌ Ошибка: {result}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
