import os, requests, asyncio, aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiocryptopay import AioCryptoPay, Networks

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
CRYPTO_TOKEN = os.getenv("CRYPTO_TOKEN")
BASE_URL = "https://api.greedy-sms.com"
MARKUP = 25.0

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
crypto = AioCryptoPay(token=CRYPTO_TOKEN, network=Networks.MAIN_NET)

class States(StatesGroup):
    waiting_for_amount = State()
    search = State()

async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0)")
        await db.commit()

def get_flag(c): return "".join([chr(127397 + ord(char)) for char in c.upper()]) if c else "🌐"

def get_countries():
    r = requests.post(f"{BASE_URL}/activations/getCountries", json={"page": 1, "pageSize": 100}, headers={"Content-Type": "application/json", "x-api-key": API_KEY})
    return r.json().get("countries", []) if r.status_code == 200 else []

def get_prices():
    r = requests.post(f"{BASE_URL}/activations/getPrices", json={"service": "tg", "page": 1, "pageSize": 100}, headers={"Content-Type": "application/json", "x-api-key": API_KEY})
    m = {}
    if r.status_code == 200:
        for i in r.json().get("countries", []):
            for s in i.get("services", []):
                if s.get("name") == "tg": m[i["country"]] = s.get("price", 0)
    return m
    
    def get_kb(page=1, sort=False, query=None):
         items = []
         prices = get_prices()
         for c in get_countries():
             p = prices.get(c['id'], 0)
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
    kb.append([InlineKeyboardButton(text="⏮", callback_data=f"p_1_{sort}"), InlineKeyboardButton(text="⬅️", callback_data=f"p_{page-1}_{sort}"), InlineKeyboardButton(text=f"{page}/{total}", callback_data="none"), InlineKeyboardButton(text="➡️", callback_data=f"p_{page+1}_{sort}"), InlineKeyboardButton(text="⏭", callback_data=f"p_{total}_{sort}")])
    kb.append([InlineKeyboardButton(text="💰 Сортировать" if not sort else "↕️ Обычный", callback_data=f"sort_{not sort}")])
    kb.append([InlineKeyboardButton(text="🔎 Поиск", callback_data="start_search")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start(m: Message):
    await m.answer("Добро пожаловать!", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🌍 Купить номер"), KeyboardButton(text="👤 Профиль")], [KeyboardButton(text="💰 Пополнить")]], resize_keyboard=True))

@dp.message(F.text == "💰 Пополнить")
async def top_up(m: Message, state: FSMContext):
    await m.answer("Введите сумму в USDT:")
    await state.set_state(States.waiting_for_amount)

@dp.message(States.waiting_for_amount)
async def create_inv(m: Message, state: FSMContext):
    inv = await crypto.create_invoice(asset='USDT', amount=float(m.text))
    await m.answer("Оплатите счет:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Оплатить", url=inv.pay_url)]]))
    await state.clear()

@dp.message(F.text == "👤 Профиль")
async def prof(m: Message):
    async with aiosqlite.connect("bot.db") as db:
        user = await db.execute_fetchone("SELECT balance FROM users WHERE id=?", (m.from_user.id,))
        bal = user[0] if user else 0
        await m.answer(f"👤 Ваш профиль\n💰 Баланс: {bal} ₽")

@dp.callback_query(F.data.startswith("p_"))
async def pag(c: CallbackQuery):
    _, p, s = c.data.split("_")
    await c.message.edit_reply_markup(reply_markup=get_kb(int(p), s=="True"))
    await c.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def buy(c: CallbackQuery):
    _, id, p = c.data.split("_")
    await c.message.answer(f"Купить страну ID {id} за {p} ₽?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Да", callback_data=f"conf_{id}_{p}")]]))

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__": asyncio.run(main())
    
