import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- Настройки ---
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.greedy-sms.com"
MARKUP = 25.0  # Твоя наценка

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Состояния ---
class SearchState(StatesGroup):
    waiting_for_country = State()

# --- API Функции ---
def get_countries_from_api():
    headers = {"Content-Type": "application/json", "x-api-key": API_KEY}
    response = requests.post(f"{BASE_URL}/activations/getCountries", json={"page": 1, "pageSize": 100}, headers=headers)
    return response.json().get("countries", []) if response.status_code == 200 else []

def get_prices_map(service_name="tg"):
    headers = {"Content-Type": "application/json", "x-api-key": API_KEY}
    response = requests.post(f"{BASE_URL}/activations/getPrices", json={"service": service_name}, headers=headers)
    prices_map = {}
    if response.status_code == 200:
        data = response.json()
        for item in data.get("countries", []):
            # Отладочная строка для логов
            print(f"DEBUG: Services for country {item.get('country')}: {item.get('services')}")
            
            for s in item.get("services", []):
                if s.get("name") == service_name:
                    prices_map[item["country"]] = s.get("price", 0)
    return prices_map

# --- Клавиатура ---
def get_countries_kb(page=1, search_query=None):
    all_countries = get_countries_from_api()
    prices_map = get_prices_map("tg")
    
    if search_query:
        all_countries = [c for c in all_countries if search_query.lower() in c['title']['rus'].lower()]
    
    items_per_page = 8
    total_pages = (len(all_countries) + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    page_countries = all_countries[start : start + items_per_page]
    
    kb = []
    for c in page_countries:
        c_id = c['id']
        raw_price = prices_map.get(c_id, 0)
        final_price = float(raw_price) + MARKUP
        
        button_text = f"{c['title']['rus']} — {final_price:.2f} ₽"
        kb.append([InlineKeyboardButton(text=button_text, callback_data=f"buy_{c_id}_{final_price:.2f}")])
    
    nav = []
    if page > 1: nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page-1}"))
    if page < total_pages: nav.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page+1}"))
    if nav: kb.append(nav)
    
    kb.append([InlineKeyboardButton(text="🔎 Поиск страны", callback_data="start_search")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- Обработчики ---
@dp.message(Command("start"))
async def start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🌍 Список стран")]], resize_keyboard=True)
    await message.answer("👋 Добро пожаловать!", reply_markup=kb)

@dp.message(F.text == "🌍 Список стран")
async def show_list(message: Message):
    await message.answer("🌍 Выберите страну:", reply_markup=get_countries_kb(page=1))

@dp.callback_query(F.data.startswith("page_"))
async def change_page(call: CallbackQuery):
    page = int(call.data.split("_")[1])
    await call.message.edit_reply_markup(reply_markup=get_countries_kb(page=page))
    await call.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def ask_confirm(call: CallbackQuery):
    _, country_id, price = call.data.split("_")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{country_id}_{price}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_search")]
    ])
    await call.message.answer(f"💰 Цена номера: {price} ₽.\nПодтвердить покупку?", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_purchase(call: CallbackQuery):
    _, country_id, price = call.data.split("_")
    await call.message.answer(f"✅ Запрос на покупку (ID {country_id}) за {price} ₽ принят!")
    await call.answer()

@dp.callback_query(F.data == "start_search")
async def start_search(call: CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.waiting_for_country)
    await call.message.answer("⌨️ Введите название страны:")
    await call.answer()

@dp.message(SearchState.waiting_for_country)
async def process_search(message: Message, state: FSMContext):
    await message.answer(f"🔎 Результаты:", reply_markup=get_countries_kb(page=1, search_query=message.text))
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
