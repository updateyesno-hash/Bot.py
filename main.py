import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Настройки
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.greedy-sms.com"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь ID -> Эмодзи флагов
COUNTRY_FLAGS = {
    1: "🇺🇦", 2: "🇰🇿", 3: "🇨🇳", 4: "🇵🇭", 5: "🇲🇲", 6: "🇮🇩", 7: "🇲🇾", 
    8: "🇰🇪", 9: "🇹🇿", 10: "🇻🇳", 11: "🇰🇬", 13: "🇮🇱", 14: "🇭🇰", 
    15: "🇵🇱", 16: "🇬🇧", 17: "🇲🇬", 18: "🇨🇩", 19: "🇳🇬", 20: "🇲🇴", 
    21: "🇪🇬", 22: "🇮🇳", 23: "🇮🇪", 24: "🇰🇭", 25: "🇱🇦", 26: "🇭🇹", 
    27: "🇨🇮", 28: "🇬🇲", 29: "🇷🇸", 30: "🇾🇪", 31: "🇿🇦", 32: "🇷🇴", 
    33: "🇨🇴", 34: "🇪🇪", 35: "🇦🇿", 36: "🇨🇦", 37: "🇲🇦", 38: "🇬🇭", 
    39: "🇦🇷", 40: "🇺🇿", 41: "🇨🇲", 42: "🇹🇩", 43: "🇩🇪", 44: "🇱🇹", 
    45: "🇭🇷", 46: "🇸🇪", 47: "🇮🇶", 48: "🇳🇱", 49: "🇱🇻", 50: "🇦🇹", 51: "🇧🇾"
}

# Функция отправки API запросов
def send_api_request(endpoint, data=None):
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    url = f"{BASE_URL}/{endpoint}"
    response = requests.post(url, json=data or {}, headers=headers)
    return response.status_code, response.json()

# Команда /start
@dp.message(Command("start"))
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить номер TG", callback_data="buy_tg")],
        [InlineKeyboardButton(text="🌍 Список стран", callback_data="list_countries")]
    ])
    await message.answer("👋 Привет! Выберите действие:", reply_markup=kb)

# Список стран
@dp.callback_query(F.data == "list_countries")
async def show_countries(callback: CallbackQuery):
    status, result = send_api_request("activations/getCountries", {"page": 1, "pageSize": 60})
    
    if status == 200:
        text = "🌍 **Доступные страны:**\n\n"
        for c in result.get("countries", []):
            flag = COUNTRY_FLAGS.get(c['id'], "🏳️")
            text += f"{flag} {c['title']['rus']} (ID: {c['id']})\n"
        
        # Отправляем частями, если список очень длинный
        if len(text) > 4096:
            await callback.message.answer(text[:4096])
            await callback.message.answer(text[4096:])
        else:
            await callback.message.answer(text)
    else:
        await callback.message.answer("❌ Ошибка при получении списка стран.")
    await callback.answer()

# Покупка номера (пример для TG)
@dp.callback_query(F.data == "buy_tg")
async def buy_number(callback: CallbackQuery):
    # country=1 (Украина согласно твоему списку), service='tg'
    status, result = send_api_request("activations/getNumber", {"service": "tg", "country": 1})
    
    if status == 200 and "activationId" in result:
        await callback.message.answer(f"✅ Номер: {result['phone']}\n🆔 ID активации: {result['activationId']}")
    else:
        await callback.message.answer(f"❌ Ошибка: {result.get('message', 'Не удалось получить номер')}")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
