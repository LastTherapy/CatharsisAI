import asyncio
import logging
import os, sys
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers.commands import router as commands_router
from handlers.messages import router as message_router

load_dotenv()


async def main():
    bot = Bot(token=os.getenv('TG_TOKEN'))
    dp = Dispatcher()
    dp.include_router(commands_router)
    dp.include_router(message_router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    asyncio.run(main())