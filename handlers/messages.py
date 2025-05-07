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


# In-memory chat histories: { chat_id: [ {"role":"user"/"assistant", "content":...}, ... ] }
chat_histories: dict[int, list[dict]] = {}


@router.message(F.text, F.chat.type == "private")
async def handle_chat(message: Message):
    bot = message.bot
    chat_id = message.chat.id
    # Добавляем сообщение пользователя в историю
    history = chat_histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": message.text})

    # Отправляем плейсхолдер-ответ
    sent = await message.reply("⏳ thinking...")

    # Получаем асинхронный итератор чанков (await обязательный)
    stream = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        stream=True
    )

    buffer = ""  # накопленный текст для редактирования
    debounce_task = None  # задача-дебаунсер

    async def debounce_flush():
        nonlocal buffer
        # Ждём 1 секунду перед первым редактированием
        await asyncio.sleep(1)
        text_to_send = buffer
        buffer = ""
        try:
            await message.bot.edit_message_text(
                text=text_to_send,
                chat_id=chat_id,
                message_id=sent.message_id
            )
        except TelegramRetryAfter as e:
            # если вернули retry_after — ждём и повторяем
            await asyncio.sleep(e.retry_after)
            await message.bot.edit_message_text(
                text=text_to_send,
                chat_id=chat_id,
                message_id=sent.message_id
            )
        except TelegramBadRequest as e:
            # если вернули 400 — не редактируем
            print(e)
            pass

    async for chunk in stream:
        delta = chunk.choices[0].delta.content  # прирост текста
        if not delta:
            continue

        buffer += delta

        # Если раньше не запущен дебаунсер — запускаем
        if debounce_task is None or debounce_task.done():
            debounce_task = asyncio.create_task(debounce_flush())

    # После завершения потока — дожидаемся последнего фтапа debounce
    if debounce_task:
        await debounce_task

    # Сохраняем ответ ассистента
    history.append({"role": "assistant", "content": buffer})