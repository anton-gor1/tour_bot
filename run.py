import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from app.handlers import router
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())