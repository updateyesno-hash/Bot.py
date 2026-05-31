import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.greedy-sms.com"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище: {user_id: {"activation_id": ..., "status": ...}}
user_activations = {}

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

# Клавиатура подтверждения покупки
def confirm_kb(country_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить покупку", callback_data=f"confirm_{country_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_buy")]
    ])

# --- ОБРАБОТЧИКИ ---

@dp.message(F.text == "🛒 Купить номер")
async def show_countries(message: Message):
    await message.answer("Напиши название страны, чтобы найти её:")

@dp.message(F.text == "💰 Баланс")
async def check_balance(message: Message):
    status, result = send_api_request("users/getBalance")
    await message.answer(f"💵 Баланс: {result.get('balance', '0')} руб." if status == 200 else "Ошибка.")

@dp.message()
async def search_and_buy(message: Message):
    # Поиск страны
    status, result = send_api_request("activations/getCountries", {"page": 1, "pageSize": 100})
    countries = [c for c in result.get("countries", []) if message.text.lower() in c['title']['rus'].lower()]
    
    if not countries:
        await message.answer("❌ Страна не найдена.")
        return

    c = countries[0]
    await message.answer(f"Вы выбрали: {c['title']['rus']}.\nПодтверждаете покупку?", reply_markup=confirm_kb(c['id']))

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_purchase(callback: CallbackQuery):
    country_id = callback.data.split("_")[1]
    status, result = send_api_request("activations/getNumber", {"service": "tg", "country": int(country_id), "operator": "any"})
    
    if status == 200:
        act_id = result['activationId']
        user_activations[callback.from_user.id] = {"act_id": act_id, "status": "pending"}
        await callback.message.answer(f"✅ Номер: {result['phone']}\n🆔 ID: {act_id}\n\nОжидаю SMS...\nИспользуй /check для проверки.")
    else:
        await callback.message.answer("❌ Ошибка покупки.")
    await callback.answer()

@dp.message(Command("check"))
async def check_sms(message: Message):
    user_id = message.from_user.id
    if user_id not in user_activations:
        return await message.answer("У вас нет активных заказов.")
    
    act_id = user_activations[user_id]["act_id"]
    status, result = send_api_request("activations/getStatus", {"activationId": act_id})
    
    # Если статус 'received' или 'success' - код пришел
    if result.get("status") in ["received", "success"]:
        user_activations[user_id]["status"] = "received"
        await message.answer(f"📩 Код: {result.get('sms')}")
    else:
        await message.answer("⏳ Код еще не пришел.")

@dp.message(Command("cancel"))
async def cancel_order(message: Message):
    user_id = message.from_user.id
    if user_id not in user_activations:
        return await message.answer("Нет активных заказов.")
    
    # ЛОГИКА: если код пришел, отмена запрещена
    if user_activations[user_id]["status"] == "received":
        await message.answer("⛔ Отмена невозможна: код уже получен!")
    else:
        act_id = user_activations[user_id]["act_id"]
        send_api_request("activations/setStatus", {"activationId": act_id, "status": "cancel"})
        del user_activations[user_id]
        await message.answer("✅ Заказ отменен.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
