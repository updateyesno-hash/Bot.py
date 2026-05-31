import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# 1. Настройки и инициализация
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
# СНАЧАЛА создаем Dispatcher
dp = Dispatcher(storage=MemoryStorage())

# 2. Состояния (FSM)
class ShopStates(StatesGroup):
    searching = State()

# 3. Клавиатуры
def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🛒 Купить"), KeyboardButton(text="🌍 Список стран")],
        [KeyboardButton(text="👤 Профиль")]
    ], resize_keyboard=True)

# 4. ОБРАБОТЧИКИ (теперь 'dp' существует, ошибок не будет)

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Добро пожаловать!", reply_markup=get_main_kb())

@dp.message(F.text == "👤 Профиль")
async def profile_menu(message: Message):
    await message.answer("👤 Личный профиль\n💰 Баланс: 0.29 ₽")

@dp.message(F.text == "🌍 Список стран")
async def countries_menu(message: Message):
    await message.answer("Выберите действие:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Начать поиск", callback_data="start_search")]
    ]))

@dp.callback_query(F.data == "start_search")
async def request_search(call: CallbackQuery, state: FSMContext):
    await state.set_state(ShopStates.searching)
    await call.message.answer("⌨️ Введите название страны:")

@dp.message(ShopStates.searching)
async def perform_search(message: Message, state: FSMContext):
    await message.answer(f"🔎 Ищем: {message.text}")
    await state.clear()

# 5. Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
