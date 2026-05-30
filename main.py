import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

# Токен вшит, но лучше в будущем вынести в переменные окружения
TOKEN = "8003400310:AAGdd-IG-h--X1P0RBqemUglElRj9QMSrI8"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРА ---
def get_main_kb():
    # Создаем 2 кнопки
    builder = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить номер", callback_data="buy_number")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])
    return builder

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Привет! Я готов к работе. Выбери пункт меню:", reply_markup=get_main_kb())

@dp.callback_query(F.data == "buy_number")
async def buy_number_handler(callback: CallbackQuery):
    await callback.message.answer("Запрос к API: получение номера... (здесь будет вызов SMS-сервиса)")
    await callback.answer() # Убирает "часики" загрузки на кнопке

@dp.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery):
    await callback.message.answer("Ваш баланс: 0 руб.")
    await callback.answer()

# --- ЗАПУСК ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
