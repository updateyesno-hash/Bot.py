import os
import asyncio
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.greedy-sms.com"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class SearchState(StatesGroup):
    waiting_for_country = State()

def get_countries_from_api():
    headers = {"Content-Type": "application/json", "x-api-key": API_KEY}
    response = requests.post(f"{BASE_URL}/activations/getCountries", json={"page": 1, "pageSize": 100}, headers=headers)
    return response.json().get("countries", []) if response.status_code == 200 else []

def get_countries_kb(page=1, search_query=None):
    all_countries = get_countries_from_api()
    if search_query:
        all_countries = [c for c in all_countries if search_query.lower() in c['title']['rus'].lower()]
    
    items_per_page = 8
    total_pages = (len(all_countries) + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    page_countries = all_countries[start : start + items_per_page]
    
    kb = []
    for c in page_countries:
        kb.append([InlineKeyboardButton(text=c['title']['rus'], callback_data=f"buy_{c['id']}")])
    
    # Навигация
    nav = []
    if page > 1: nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page-1}"))
    if page < total_pages: nav.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page+1}"))
    kb.append(nav)
    kb.append([InlineKeyboardButton(text="🔎 Поиск страны", callback_data="start_search")])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🌍 Список стран")]], resize_keyboard=True)
    await message.answer("👋 Привет! Используй кнопку ниже.", reply_markup=kb)

@dp.message(F.text == "🌍 Список стран")
async def show_list(message: Message):
    await message.answer("🌍 Список стран:", reply_markup=get_countries_kb(page=1))

@dp.callback_query(F.data.startswith("page_"))
async def change_page(call: CallbackQuery):
    page = int(call.data.split("_")[1])
    await call.message.edit_reply_markup(reply_markup=get_countries_kb(page=page))
    await call.answer()

@dp.callback_query(F.data == "start_search")
async def start_search(call: CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.waiting_for_country)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_search")]])
    await call.message.answer("⌨️ Введите название страны:", reply_markup=cancel_kb)
    await call.answer()

@dp.message(SearchState.waiting_for_country)
async def process_search(message: Message, state: FSMContext):
    await message.answer(f"🔎 Результаты для '{message.text}':", reply_markup=get_countries_kb(page=1, search_query=message.text))
    await state.clear()

@dp.callback_query(F.data == "cancel_search")
async def cancel_search(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.answer("Поиск отменен")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
