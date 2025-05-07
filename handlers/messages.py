import os
import asyncio
from aiogram import Router, F
from aiogram.types import Message
from openai import AsyncOpenAI
from dotenv import load_dotenv
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter

load_dotenv()
router: Router = Router()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


chat_histories: dict[int, list[dict]] = {}


@router.message(F.text, F.chat.type == "private")
async def handle_chat(message: Message):
    chat_id = message.chat.id
    # 1) Сохраняем историю
    history = chat_histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": message.text})

    # 2) Плейсхолдер
    sent = await message.reply("⏳ thinking...")

    # 3) Получаем стрим (await нужен!)
    stream = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        stream=True
    )

    full_text = ""
    debounce_task: asyncio.Task | None = None

    async def schedule_flush():
        # Ждём 1 секунду перед редактированием
        try:
            await asyncio.sleep(1)
            # Используем весь накопленный full_text
            text = full_text
            await message.bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=sent.message_id
            )
        except TelegramRetryAfter as e:
            # Если телеграм вернул retry_after, ждём и повторяем
            await asyncio.sleep(e.retry_after)
            await message.bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=sent.message_id
            )
        except asyncio.CancelledError:
            # Если задачу отменили — просто выходим
            return

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if not delta:
            continue
        full_text += delta

        # Отменяем предыдущий запланированный флаш, если он ещё не выполнился
        if debounce_task and not debounce_task.done():
            debounce_task.cancel()
        # Запускаем новую задачу-дебаунсер
        debounce_task = asyncio.create_task(schedule_flush())

    # После окончания стрима — дожидаемся последнего обновления
    if debounce_task:
        try:
            await debounce_task
        except asyncio.CancelledError:
            # Если отменили его после стрима — всё равно делаем финальный флаш
            await message.bot.edit_message_text(
                text=full_text,
                chat_id=chat_id,
                message_id=sent.message_id
            )

    # 4) Сохраняем ответ ассистента
    history.append({"role": "assistant", "content": full_text})
