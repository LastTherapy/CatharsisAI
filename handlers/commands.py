from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router: Router = Router()


@router.message(Command('start'))
async def cmd_start(message: Message):
    await message.answer('Бот предоставляет доступ к chatgpt 4.1 - модели, доступной только по api')


@router.message(Command('balance'))
async def cmd_balance(message: Message):
    await message.answer('Ваш баланс 0 рублей')