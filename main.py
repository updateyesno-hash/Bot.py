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
MARKUP = 25.0 

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class SearchState(StatesGroup):
    waiting_for_country = State()

def get_countries_from_api():
    headers = {"Content-Type": "application/json", "x-api-key": API_KEY}
    response = requests.post(f"{BASE_URL}/activations/getCountries", json={"page": 1, "pageSize": 100}, headers=headers)
    return response.json().get("countries", []) if response.status_code == 200 else []

def get_prices_map(service_name="tg"):
    headers = {"Content-Type": "application/json", "x-api-key": API_KEY}
    payload = {"service": service_name, "page": 1, "pageSize": 100}
    try:
        response = requests.post(f"{BASE_URL}/activations/getPrices", json=payload, headers=headers)
        prices_map = {}
        if response.status_code == 200:
            data = response.json()
            for item in data.get("countries", []):
                for s in item.get("services", []):
                    if s.get("name") == service_name:
                        prices_map[item["country"]] = s.get("price", 0)
        return prices_map
    except Exception:
        return {}

def get_countries_kb(page=1, search_query=None):
    all_countries = get_countries_from_api()
    prices_map = get_prices_map("tg")
    
    # ФИЛЬТРАЦИЯ: оставляем только те страны, где есть цена
    available_countries = []
    for c in all_countries:
        c_id = c['id']
        price = prices_map.get(c_id, 0)
        if price > 0: # Только если цена > 0
            c['final_price'] = float(price) + MARKUP
            available_countries.append(c)
    
    if search_query:
        available_countries = [c for c in available_countries if search_query.lower() in c['title']['rus'].lower()]
    
    items_per_page = 8
    total_pages = (len(available_countries) + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    page_countries = available_countries[start : start + items_per_page]
    
    kb = []
    for c in page_countries:
        c_id = c['id']
        price = c['final_price']
        button_text = f"{c['title']['rus']} — {price:.2f} ₽"
        kb.append([InlineKeyboardButton(text=button_text, callback_data=f"buy_{c_id}_{price:.2f}")])
    
    nav = []
    if page > 1: nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page-1}"))
    if page < total_pages: nav.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page+1}"))
    if nav: kb.append(nav)
    kb.append([InlineKeyboardButton(text="🔎 Поиск", callback_data="start_search")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🌍 Список стран")]], resize_keyboard=True)
    await message.answer("👋 Привет! Выберите страну для покупки:", reply_markup=kb)

@dp.message(F.text == "🌍 Список стран")
async def show_list(message: Message):
    await message.answer("🌍 Доступные страны:", reply_markup=get_countries_kb())

@dp.callback_query(F.data.startswith("page_"))
async def change_page(call: CallbackQuery):
    page = int(call.data.split("_")[1])
    await call.message.edit_reply_markup(reply_markup=get_countries_kb(page=page))
    await call.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def ask_confirm(call: CallbackQuery):
    _, c_id, price = call.data.split("_")
    await call.message.answer(f"💰 Цена: {price} ₽.\nПодтвердить?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Да, купить", callback_data=f"confirm_{c_id}_{price}")]]))
    await call.answer()

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_purchase(call: CallbackQuery):
    _, c_id, price = call.data.split("_")
    await call.message.answer(f"✅ Запрос на покупку принят! (ID {c_id}, Цена {price})")
    await call.answer()

@dp.callback_query(F.data == "start_search")
async def start_search(call: CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.waiting_for_country)
    await call.message.answer("⌨️ Введите название страны:")
    await call.answer()

@dp.message(SearchState.waiting_for_country)
async def process_search(message: Message, state: FSMContext):
    await message.answer("🔎 Результаты поиска:", reply_markup=get_countries_kb(search_query=message.text))
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
