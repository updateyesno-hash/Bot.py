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

# --- Вспомогательные функции ---
def get_flag(country_code):
    country_code = country_code.upper()
    return "".join([chr(127397 + ord(char)) for char in country_code])

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
            for item in response.json().get("countries", []):
                for s in item.get("services", []):
                    if s.get("name") == service_name:
                        prices_map[item["country"]] = s.get("price", 0)
        return prices_map
    except:
        return {}

def get_countries_kb(page=1, search_query=None):
    all_countries = get_countries_from_api()
    prices_map = get_prices_map("tg")
    
    items = []
    for c in all_countries:
        price = prices_map.get(c['id'], 0)
        if price > 0:
            c['final_price'] = float(price) + MARKUP
            items.append(c)
    
    if search_query:
        items = [c for c in items if search_query.lower() in c['title']['rus'].lower()]
    
    per_page = 8
    total_pages = max(1, (len(items) + per_page - 1) // per_page)
    start = (page - 1) * per_page
    page_items = items[start : start + per_page]
    
    kb = []
    for c in page_items:
        flag = get_flag(c.get('iso', 'xx'))
        text = f"{flag} {c['title']['rus']} — {c['final_price']:.2f} ₽"
        kb.append([InlineKeyboardButton(text=text, callback_data=f"buy_{c['id']}_{c['final_price']:.2f}")])
    
    nav = []
    if page > 1: nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="none"))
    if page < total_pages: nav.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page+1}"))
    if nav: kb.append(nav)
    
    kb.append([InlineKeyboardButton(text="🔎 Поиск", callback_data="start_search")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- Обработчики меню ---
@dp.message(Command("start"))
async def start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🌍 Купить номер"), KeyboardButton(text="👤 Профиль")]
    ], resize_keyboard=True)
    await message.answer("👋 Добро пожаловать!", reply_markup=kb)

@dp.message(F.text == "🌍 Купить номер")
async def show_list(message: Message):
    await message.answer("Выберите страну:", reply_markup=get_countries_kb(1))

# --- Callback-обработчики ---
@dp.callback_query(F.data.startswith("page_"))
async def change_page(call: CallbackQuery):
    page = int(call.data.split("_")[1])
    await call.message.edit_reply_markup(reply_markup=get_countries_kb(page))
    await call.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def buy(call: CallbackQuery):
    _, c_id, price = call.data.split("_")
    await call.message.answer(f"✅ Вы выбрали страну ID {c_id}. Цена: {price} ₽. Подтвердить?")
    await call.answer()

@dp.callback_query(F.data == "start_search")
async def start_search(call: CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.waiting_for_country)
    await call.message.answer("⌨️ Введите название:")
    await call.answer()

@dp.message(SearchState.waiting_for_country)
async def process_search(message: Message, state: FSMContext):
    await message.answer("🔎 Результаты:", reply_markup=get_countries_kb(1, message.text))
    await state.clear()

@dp.callback_query(F.data == "none")
async def none(call: CallbackQuery):
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
