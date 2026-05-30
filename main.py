import asyncio
import os
from aiogram import Bot, Dispatcher

TOKEN = "8003400310:AAGdd-IG-h--X1P0RBqemUglElRj9QMSrI8"

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Теперь эта команда внутри функции, ошибки не будет
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
