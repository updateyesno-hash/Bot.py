import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.greedy-sms.com"
MARKUP = 25.0

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class SearchState(StatesGroup):
    waiting_for_country = State()

def get_flag(c): return "".join([chr(127397 + ord(char)) for char in c.upper()]) if c else "🌐"

def get_countries_from_api():
    r = requests.post(f"{BASE_URL}/activations/getCountries", json={"page": 1, "pageSize": 100}, headers={"Content-Type": "application/json", "x-api-key": API_KEY})
    return r.json().get("countries", []) if r.status_code == 200 else []

def get_prices_map():
    r = requests.post(f"{BASE_URL}/activations/getPrices", json={"service": "tg", "page": 1, "pageSize": 100}, headers={"Content-Type": "application/json", "x-api-key": API_KEY})
    m = {}
    if r.status_code == 200:
        for i in r.json().get("countries", []):
            for s in i.get("services", []):
                if s.get("name") == "tg": m[i["country"]] = s.get("price", 0)
    return m

def get_kb(page=1, sort=False, query=None):
    all_c = get_countries_from_api()
    p_map = get_prices_map()
    items = []
    for c in all_c:
        p = p_map.get(c['id'], 0)
        if p > 0:
            c['fp'] = float(p) + MARKUP
            items.append(c)
    if query: items = [c for c in items if query.lower() in c['title']['rus'].lower()]
    if sort: items.sort(key=lambda x: x['fp'])
    
    per_page = 8
    total = max(1, (len(items) + per_page - 1) // per_page)
    page = max(1, min(page, total))
    start = (page - 1) * per_page
    
    kb = [[InlineKeyboardButton(text=f"{get_flag(c.get('iso'))} {c['title']['rus']} — {c['fp']:.2f} ₽", callback_data=f"buy_{c['id']}_{c['fp']:.2f}")] for c in items[start:start+per_page]]
    nav = [InlineKeyboardButton(text="⏮", callback_data=f"p_1_{sort}"), InlineKeyboardButton(text="⬅️", callback_data=f"p_{page-1}_{sort}"), InlineKeyboardButton(text=f"{page}/{total}", callback_data="none"), InlineKeyboardButton(text="➡️", callback_data=f"p_{page+1}_{sort}"), InlineKeyboardButton(text="⏭", callback_data=f"p_{total}_{sort}")]
    kb.append(nav)
    kb.append([InlineKeyboardButton(text="💰 Сортировать" if not sort else "↕️ Обычный", callback_data=f"sort_{not sort}")])
    kb.append([InlineKeyboardButton(text="🔎 Поиск", callback_data="start_search")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start(m: Message):
    await m.answer("Добро пожаловать!", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🌍 Купить номер"), KeyboardButton(text="👤 Профиль")]], resize_keyboard=True))

@dp.message(F.text == "🌍 Купить номер")
async def show(m: Message): await m.answer("Выберите страну:", reply_markup=get_kb())

@dp.message(F.text == "👤 Профиль")
async def prof(m: Message): await m.answer("👤 Профиль\n💰 Баланс: 0 ₽")

@dp.callback_query(F.data.startswith("p_"))
async def pag(c: CallbackQuery):
    _, p, s = c.data.split("_")
    await c.message.edit_reply_markup(reply_markup=get_kb(int(p), s=="True"))
    await c.answer()

@dp.callback_query(F.data.startswith("sort_"))
async def srt(c: CallbackQuery):
    await c.message.edit_reply_markup(reply_markup=get_kb(1, c.data.split("_")[1]=="True"))
    await c.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def buy(c: CallbackQuery):
    _, id, p = c.data.split("_")
    await c.message.answer(f"Подтвердить покупку за {p} ₽?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{id}_{p}")]]))
    await c.answer()

@dp.callback_query(F.data == "start_search")
async def srch(c: CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.waiting_for_country)
    await c.message.answer("Введите название:")

@dp.message(SearchState.waiting_for_country)
async def proc_srch(m: Message, state: FSMContext):
    await m.answer("Результаты:", reply_markup=get_kb(1, False, m.text))
    await state.clear()

@dp.callback_query(F.data == "none")
async def none(c: CallbackQuery): await c.answer()

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
    
