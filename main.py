import os, requests, asyncio, aiosqlite
from aiohttp import web
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

def get_kb(page=1, sort=False):
    items = []
    prices = get_prices()
    for c in get_countries():
        p = prices.get(c['id'], 0)
        if p > 0:
            c['fp'] = float(p) + MARKUP
            items.append(c)
    if sort: items.sort(key=lambda x: x['fp'])
    
    per_page = 8
    total = max(1, (len(items) + per_page - 1) // per_page)
    page = max(1, min(page, total))
    start = (page - 1) * per_page
    
    kb = [[InlineKeyboardButton(text=f"{get_flag(c.get('iso'))} {c['title']['rus']} — {c['fp']:.2f} ₽", callback_data=f"buy_{c['id']}")] for c in items[start:start+per_page]]
    kb.append([InlineKeyboardButton(text="⬅️", callback_data=f"p_{page-1}_{sort}"), InlineKeyboardButton(text=f"{page}/{total}", callback_data="none"), InlineKeyboardButton(text="➡️", callback_data=f"p_{page+1}_{sort}")])
    kb.append([InlineKeyboardButton(text="💰 Сортировать" if not sort else "↕️ Обычный", callback_data=f"sort_{not sort}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)
async def webhook_handler(request):
    data = await request.post()
    if data.get('status') == 'paid':
        user_id = int(data.get('description'))
        amount = float(data.get('amount'))
        async with aiosqlite.connect("bot.db") as db:
            await db.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
            await db.commit()
            await bot.send_message(user_id, "✅ Баланс пополнен!")
    return web.Response(status=200)

@dp.message(Command("start"))
async def start(m: Message):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (m.from_user.id,))
        await db.commit()
    await m.answer("Добро пожаловать!", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🌍 Купить номер"), KeyboardButton(text="👤 Профиль")], [KeyboardButton(text="💰 Пополнить")]], resize_keyboard=True))

@dp.message(F.text == "🌍 Купить номер")
async def show(m: Message): await m.answer("Выберите страну:", reply_markup=get_kb())

@dp.message(F.text == "👤 Профиль")
async def prof(m: Message):
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute("SELECT balance FROM users WHERE id=?", (m.from_user.id,))
        row = await cursor.fetchone()
        bal = row[0] if row else 0
        await m.answer(f"👤 Ваш профиль\n💰 Баланс: {bal} ₽")

@dp.message(F.text == "💰 Пополнить")
async def top_up(m: Message, state: FSMContext):
    await m.answer("Введите сумму в USDT:")
    await state.set_state(States.waiting_for_amount)

@dp.message(States.waiting_for_amount)
async def create_inv(m: Message, state: FSMContext):
    inv = await crypto.create_invoice(asset='USDT', amount=float(m.text), description=str(m.from_user.id))
    await m.answer(f"Оплатите счет: {inv.pay_url}")
    await state.clear()

@dp.callback_query(F.data.startswith("p_"))
async def pag(c: CallbackQuery):
    _, p, s = c.data.split("_")
    await c.message.edit_reply_markup(reply_markup=get_kb(int(p), s=="True"))
    await c.answer()

async def main():
    await init_db()
    app = web.Application()
    app.router.add_post('/webhook', webhook_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__": asyncio.run(main())
    
