import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Настройки (убедись, что переменные добавлены в Railway)
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.greedy-sms.com"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Функция запроса к API
def send_api_request(endpoint, data=None):
    headers = {"Content-Type": "application/json", "x-api-key": API_KEY}
    response = requests.post(f"{BASE_URL}/{endpoint}", json=data or {}, headers=headers)
    return response.status_code, response.json()

# Генерация клавиатуры со странами (пагинация + поиск)
async def get_countries_keyboard(page=1, search_query=None):
    status, result = send_api_request("activations/getCountries", {"page": 1, "pageSize": 100})
    if status != 200: return None
    
    countries = result.get("countries", [])
    if search_query:
        countries = [c for c in countries if search_query.lower() in c['title']['rus'].lower()]
    
    # Пагинация (по 10 на страницу)
    start = (page - 1) * 10
    end = start + 10
    page_countries = countries[start:end]
    
    buttons = [[InlineKeyboardButton(text=c['title']['rus'], callback_data=f"buy_{c['id']}")] for c in page_countries]
    
    # Навигация
    nav = []
    if page > 1: nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"list_{page-1}"))
    if end < len(countries): nav.append(InlineKeyboardButton(text="➡️", callback_data=f"list_{page+1}"))
    if nav: buttons.append(nav)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Команда /start
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("👋 Привет! Напиши название страны для поиска или введи /countries, чтобы увидеть весь список.")

# Список стран
@dp.message(Command("countries"))
@dp.callback_query(F.data.startswith("list_"))
async def show_countries(call_or_msg):
    page = int(call_or_msg.data.split("_")[1]) if isinstance(call_or_msg, CallbackQuery) else 1
    kb = await get_countries_keyboard(page)
    
    if isinstance(call_or_msg, CallbackQuery):
        await call_or_msg.message.edit_text("🌍 Выберите страну:", reply_markup=kb)
    else:
        await call_or_msg.answer("🌍 Выберите страну:", reply_markup=kb)

# Поиск страны
@dp.message()
async def search_country(message: Message):
    kb = await get_countries_keyboard(page=1, search_query=message.text)
    if not kb or not kb.inline_keyboard:
        await message.answer("❌ Страна не найдена.")
    else:
        await message.answer(f"🔎 Результаты поиска для '{message.text}':", reply_markup=kb)

# Покупка номера
@dp.callback_query(F.data.startswith("buy_"))
async def buy_number(callback: CallbackQuery):
    country_id = callback.data.split("_")[1]
    status, result = send_api_request("activations/getNumber", {"service": "tg", "country": country_id})
    
    if status == 200:
        await callback.message.answer(f"✅ Номер получен:\n📞 {result['phone']}\n🆔 ID активации: {result['activationId']}")
    elif status == 500 and result.get('message') == 'No numbers available':
        await callback.message.answer("⚠️ Номера для этой страны закончились.")
    else:
        await callback.message.answer(f"❌ Ошибка: {result.get('message', 'Неизвестная ошибка')}")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
