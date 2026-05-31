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

# --- Вспомогательная функция для флагов ---
def get_flag(country_code):
    # Преобразует код страны (например, 'ru') в эмодзи флага
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
    except Exception:
        return {}

def get_countries_kb(page=1, search_query=None):
    all_countries = get_countries_from_api()
    prices_map = get_prices_map("tg")
    
    available_countries = []
    for c in all_countries:
        c_id = c['id']
        price = prices_map.get(c_id, 0)
        if price > 0:
            c['final_price'] = float(price) + MARKUP
            available_countries.append(c)
    
    if search_query:
        available_countries = [c for c in available_countries if search_query.lower() in c['title']['rus'].lower()]
    
    items_per_page = 8
    total_pages = (len(available_countries) + items_per_page - 1) // items_per_page
    if total_pages == 0: total_pages = 1
    
    start = (page - 1) * items_per_page
    page_countries = available_countries[start : start + items_per_page]
    
    kb = []
    for c in page_countries:
        c_id = c['id']
        # Предполагаем, что в API приходит eng код, если нет - используем '??'
        flag = get_flag(c.get('iso', '??')) 
        price = c['final_price']
        button_text = f"{flag} {c['title']['rus']} — {price:.2f} ₽"
        kb.append([InlineKeyboardButton(text=button_text, callback_data=f"buy_{c_id}_{price:.2f}")])
    
    # Навигация + Счетчик
    nav = []
    if page > 1: nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages: nav.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page+1}"))
    kb.append(nav)
    
    kb.append([InlineKeyboardButton(text="🔎 Поиск", callback_data="start_search")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- Обработчики (остались прежними, кроме callback для счетчика) ---
@dp.callback_query(F.data == "ignore")
async def ignore(call: CallbackQuery):
    await call.answer()

# ... (Остальные функции: start, show_list, change_page, buy, confirm, search - без изменений)
