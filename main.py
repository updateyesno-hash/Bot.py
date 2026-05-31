import os, requests, asyncio, aiosqlite, hashlib, hmac
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiocryptopay import AioCryptoPay, Networks

# Конфигурация
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

# --- Логика БД и API ---
async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0)")
        await db.commit()

# ... (Функции get_countries, get_prices, get_kb — оставляем прежними) ...

# --- Вебхук ---
async def webhook_handler(request):
    data = await request.post()
    # Здесь логика подтверждения подписи от CryptoPay
    if data['status'] == 'paid':
        user_id = int(data['user_id']) # При создании инвойса передавай user_id в description
        amount = float(data['amount'])
        async with aiosqlite.connect("bot.db") as db:
            await db.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
            await db.commit()
            await bot.send_message(user_id, "✅ Ваш баланс пополнен!")
    return web.Response(status=200)

# --- Обработчики ---
@dp.message(F.text == "💰 Пополнить")
async def top_up(m: Message, state: FSMContext):
    await m.answer("Введите сумму в USDT:")
    await state.set_state(States.waiting_for_amount)

@dp.message(States.waiting_for_amount)
async def create_inv(m: Message, state: FSMContext):
    # В description передаем ID пользователя, чтобы потом узнать, кому зачислить
    inv = await crypto.create_invoice(asset='USDT', amount=float(m.text), description=str(m.from_user.id))
    await m.answer(f"Оплатите счет: {inv.pay_url}")
    await state.clear()

async def main():
    await init_db()
    # Запуск веб-сервера
    app = web.Application()
    app.router.add_post('/webhook', webhook_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__": asyncio.run(main())
    
