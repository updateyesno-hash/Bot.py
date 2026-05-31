import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Настройки
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.greedy-sms.com"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояние для режима поиска
class SearchState(StatesGroup):
    waiting_for_country = State()

# Запрос к API
def send_api_request(endpoint, data=None):
    headers = {"Content-Type": "application/json", "x-api-key": API_KEY}
    response = requests.post(f"{BASE_URL}/{endpoint}", json=data or {}, headers=headers)
    return response.status_code, response.json()

# --- КЛАВИАТУРЫ ---
def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🛒 Купить номер"), KeyboardButton(text="💰 Баланс")],
        [KeyboardButton(text="🔎 Найти страну")]
    ], resize_keyboard=True)

async def get_countries_keyboard(search_query):
    status, result = send_api_request("activations/getCountries", {"page": 1, "pageSize": 100})
    if status != 200: return None
    countries = [c for c in result.get("countries", []) if search_query.lower() in c['title']['rus'].lower()]
    
    # Показываем первые 10 результатов поиска
    buttons = [[InlineKeyboardButton(text=c['title']['rus'], callback_data=f"buy_{c['id']}")] for c in countries[:10]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("👋 Привет! Используй кнопки в меню:", reply_markup=get_main_kb())

@dp.message(F.text == "💰 Баланс")
async def check_balance(message: Message):
    status, result = send_api_request("users/getBalance")
    await message.answer(f"💵 Баланс: {result.get('balance', '0')} руб." if status == 200 else "❌ Ошибка баланса.")

@dp.message(F.text == "🔎 Найти страну")
async def start_search(message: Message, state: FSMContext):
    await state.set_state(SearchState.waiting_for_country)
    await message.answer("Введите название страны:")

@dp.message(SearchState.waiting_for_country)
async def process_search(message: Message, state: FSMContext):
    kb = await get_countries_keyboard(message.text)
    if not kb or not kb.inline_keyboard:
        await message.answer("❌ Ничего не найдено.")
    else:
        await message.answer(f"Результаты для '{message.text}':", reply_markup=kb)
    await state.clear()

@dp.callback_query(F.data.startswith("buy_"))
async def ask_confirm(callback: CallbackQuery):
    country_id = callback.data.split("_")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{country_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_buy")]
    ])
    await callback.message.answer(f"Подтверждаете покупку номера (ID страны: {country_id})?", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_purchase(callback: CallbackQuery):
    country_id = int(callback.data.split("_")[1])
    status, result = send_api_request("activations/getNumber", {"service": "tg", "country": country_id, "operator": "any"})
    
    if status == 200:
        await callback.message.answer(f"✅ Номер: {result['phone']}\n🆔 ID: {result['activationId']}")
    elif status == 500:
        await callback.message.answer("⚠️ Нет свободных номеров.")
    else:
        await callback.message.answer("❌ Ошибка при покупке.")
    await callback.answer()

@dp.callback_query(F.data == "cancel_buy")
async def cancel_buy(callback: CallbackQuery):
    await callback.message.answer("❌ Покупка отменена.")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
