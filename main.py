import asyncio
from aiogram import Bot, Dispatcher

TOKEN = "8003400310:AAGdd-IG-h--X1P0RBqemUglElRj9QMSrI8"

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    print("Бот в сети!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Этот способ гарантированно работает на всех нормальных хостингах
    asyncio.run(main())
