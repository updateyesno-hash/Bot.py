import os
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- Состояния ---
class ShopStates(StatesGroup):
    searching = State()

# --- Главное меню ---
def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🛒 Купить"), KeyboardButton(text="🌍 Список стран")],
        [KeyboardButton(text="👤 Профиль")]
    ], resize_keyboard=True)

# --- 1. ПРОФИЛЬ ---
@dp.message(F.text == "👤 Профиль")
async def profile_menu(message: Message):
    # В реальном проекте здесь будет запрос к БД за данными
    balance = "0.29 ₽"
    await message.answer(
        f"👤 Личный профиль\n\n🆔 ID: {message.from_user.id}\n💰 Баланс: {balance}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Пополнить", callback_data="top_up")],
            [InlineKeyboardButton(text="📜 История покупок", callback_data="history")]
        ])
    )

# --- 2. ВЫБОР СТРАН И ПОИСК ---
@dp.message(F.text == "🌍 Список стран")
async def countries_menu(message: Message):
    await message.answer(
        "🌍 Выберите страну из списка или нажмите поиск:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Начать поиск", callback_data="start_search")],
            [InlineKeyboardButton(text="📋 Список A-Z", callback_data="list_all")]
        ])
    )

@dp.callback_query(F.data == "start_search")
async def request_search(call: CallbackQuery, state: FSMContext):
    await state.set_state(ShopStates.searching)
    await call.message.answer("⌨️ Введите название страны для поиска:")

@dp.message(ShopStates.searching)
async def perform_search(message: Message, state: FSMContext):
    # Здесь логика фильтрации списка стран по message.text
    search_query = message.text
    await message.answer(f"🔎 Результаты поиска для: {search_query}")
    await state.clear() # Выходим из состояния поиска

# --- 3. ПОКУПКА ---
@dp.message(F.text == "🛒 Купить")
async def buy_menu(message: Message):
    await message.answer("Выберите сервис:") # Тут список кнопок сервисов
