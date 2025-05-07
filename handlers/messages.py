import os
import asyncio
from aiogram import Router, F
from aiogram.types import Message
from openai import AsyncOpenAI
from dotenv import load_dotenv
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
import time

load_dotenv()
router: Router = Router()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


chat_histories: dict[int, list[dict]] = {}


@router.message(F.text, F.chat.type == "private")
async def handle_chat(message: Message):
    chat_id = message.chat.id
    # 1) Сохраняем в историю
    history = chat_histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": message.text})

    # 2) Отправляем “черновик”
    sent = await message.reply("⏳")

    # 3) Запрашиваем стрим (await обязательно!)
    stream = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        stream=True
    )

    full_text = ""
    last_edit = time.monotonic()  # отметка времени последнего edit
    throttle_interval = 0.2       # минимум 200 мс между правками

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if not delta:
            continue
        full_text += delta

        now = time.monotonic()
        # если с последнего обновления прошло ≥throttle_interval
        if now - last_edit >= throttle_interval:
            try:
                await message.bot.edit_message_text(
                    text=full_text,
                    chat_id=chat_id,
                    message_id=sent.message_id
                )
                last_edit = now
            except TelegramRetryAfter as e:
                # Telegram просит подождать — спим нужное время
                await asyncio.sleep(e.retry_after)
                await message.bot.edit_message_text(
                    text=full_text,
                    chat_id=chat_id,
                    message_id=sent.message_id
                )
                last_edit = time.monotonic()

    # 4) Финальный flush (если остались недосафиксированные символы)
    if full_text and time.monotonic() - last_edit >= 0:
        await message.bot.edit_message_text(
            text=full_text,
            chat_id=chat_id,
            message_id=sent.message_id
        )

    # 5) Добавляем ответ ассистента в историю
    history.append({"role": "assistant", "content": full_text})