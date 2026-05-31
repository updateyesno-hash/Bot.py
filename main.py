import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Настройки
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

# Клавиатура меню
def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🛒 Купить номер"), KeyboardButton(text="💰 Баланс")],
        [KeyboardButton(text="🌍 Список стран")]
    ], resize_keyboard=True)

# Список стран
async def get_countries_list():
    status, result = send_api_request("activations/getCountries", {"page": 1, "pageSize": 100})
    if status != 200: 
        return None
    
    # Создаем кнопки для списка (берем первые 20 стран)
    buttons = []
    for c in result.get("countries", [])[:20]:
        buttons.append([InlineKeyboardButton(text=c['title']['rus'], callback_data=f"buy_{c['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("👋 Привет! Выберите действие в меню:", reply_markup=get_main_kb())

@dp.message(F.text == "💰 Баланс")
async def check_balance(message: Message):
    status, result = send_api_request("users/getBalance")
    if status == 200:
        await message.answer(f"💵 Баланс: {result.get('balance', '0')} руб.")
    else:
        await message.answer("❌ Ошибка при получении баланса.")

@dp.message(F.text == "🌍 Список стран")
async def show_list(message: Message):
    kb = await get_countries_list()
    if kb:
        await message.answer("🌍 Выберите страну для покупки:", reply_markup=kb)
    else:
        await message.answer("❌ Ошибка при загрузке списка.")

@dp.callback_query(F.data.startswith("buy_"))
async def ask_confirm(callback: CallbackQuery):
    country_id = callback.data.split("_")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{country_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_buy")]
    ])
    await callback.message.answer(f"Подтверждаете покупку? (ID страны: {country_id})", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_purchase(callback: CallbackQuery):
    country_id = int(callback.data.split("_")[1])
    # Делаем запрос на покупку
    status, result = send_api_request("activations/getNumber", {"service": "tg", "country": country_id, "operator": "any"})
    
    if status == 200:
        await callback.message.answer(f"✅ Номер получен:\n📞 {result['phone']}\n🆔 ID: {result['activationId']}")
    elif status == 500:
        await callback.message.answer("⚠️ Номера для этой страны закончились.")
    else:
        await callback.message.answer(f"❌ Ошибка: {result.get('message', 'Неизвестная ошибка')}")
    await callback.answer()

@dp.callback_query(F.data == "cancel_buy")
async def cancel_buy(callback: CallbackQuery):
    await callback.message.answer("❌ Покупка отменена.")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
