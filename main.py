import asyncio
import os
from aiogram import Bot, Dispatcher

# Берем токен из переменных окружения Railway (Environment Variables)
TOKEN = os.getenv("TOKEN")

async def main():
    # Создаем объекты
    bot = Bot(token='8003400310:AAGdd-IG-h--X1P0RBqemUglElRj9QMSrI8')
    dp = Dispatcher()
    
    # ПРАВИЛЬНОЕ МЕСТО: внутри функции, перед запуском polling
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("Бот успешно запущен и очищен от старых хуков!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запуск
    asyncio.run(main())
    
