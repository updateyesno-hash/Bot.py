import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Настройки
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.greedy-sms.com"

bot = Bot(token=TOKEN)
dp = Dispatcher()

def send_api_request(endpoint, data=None):
    headers = {"Content-Type": "application/json", "x-api-key": API_KEY}
    response = requests.post(f"{BASE_URL}/{endpoint}", json=data or {}, headers=headers)
    return response.status_code, response.json()

# --- КЛАВИАТУРЫ ---
def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🛒 Купить номер"), KeyboardButton(text="💰 Баланс")],
        [KeyboardButton(text="🌍 Список стран")]
    ], resize_keyboard=True)

async def get_countries_list():
    status, result = send_api_request("activations/getCountries", {"page": 1, "pageSize": 100})
    if status != 200: return None
    
    # Создаем кнопки для списка
    buttons = [[InlineKeyboardButton(text=c['title']['rus'], callback_data=f"buy_{c['id']}")] for c in result.get("countries", [])[:20]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("👋 Привет! Выберите действие:", reply_markup=get_main_kb())

@dp.message(F.text == "💰 Баланс")
async def check_balance(message: Message):
    status, result = send_api_request("users/getBalance")
    await message.answer(f"💵 Баланс: {result.get('balance', '0')} руб." if status == 200 else "❌ Ошибка.")

@dp.message(F.text == "🌍 Список стран")
async def show_list(message: Message):
    kb = await get_countries_list()
    if kb:
        await message.
        
