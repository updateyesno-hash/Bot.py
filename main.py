import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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

# --- Главное меню (нижняя панель) ---
def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🌍 Купить номер"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="💰 Пополнить"), KeyboardButton(text="❓ Помощь")]
    ], resize_keyboard=True)

# --- Логика API (остается без изменений) ---
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

# --- Генератор inline-клавиатуры для списка стран ---
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
        kb.append([InlineKeyboardButton(text=f"🌐 {c['title']['rus']} — {c['final_price']:.2f} ₽", callback_data=f"buy_{c['id']}_{c['final_price']:.2f}")])
    
    nav = []
    if page > 1: nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="none"))
    if page < total_pages: nav.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page+1}"))
    
    if nav: kb.append(nav)
    kb.append([InlineKeyboardButton(text="🔎 Поиск", callback_data="start_search")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- Обработчики меню ---
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 Привет! Я готов к работе. Выберите пункт меню ниже:", reply_markup=get_main_kb())

@dp.message(F.text == "🌍 Купить номер")
async def show_list(message: Message):
    await message.answer("Выберите страну из списка:", reply_markup=get_countries_kb(1))

@dp.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    await message.answer("👤 **Ваш профиль**\n\n🆔 ID: 123456\n💰 Баланс: 0 ₽\n🛒 Покупок: 0", parse_mode="Markdown")

@dp.message(F.text == "💰 Пополнить")
async def top_up(message: Message):
    await message.answer("💳 Для пополнения баланса переведите средства по реквизитам:\n\n`...тут будут реквизиты...`", parse_mode="Markdown")

# --- Обработка поиска и покупок (остается без изменений) ---
# (пагинация, покупка, поиск — см. предыдущий код)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
