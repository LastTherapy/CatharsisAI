import os
import asyncio
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from openai import AsyncOpenAI
from dotenv import load_dotenv
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
import time
import base64
import sqlite3
from PIL import Image
from io import BytesIO
import datetime

load_dotenv()
router: Router = Router()
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
chat_histories: dict[int, list[dict]] = {}


@router.message(F.text, F.chat.type == "private")
async def handle_chat(message: Message):
    chat_id = message.chat.id

    # 1) Сохраняем запрос пользователя
    history = chat_histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": message.text})

    # 2) Отправляем плейсхолдер с Markdown-mode
    sent = await message.reply(
        "⏳ thinking...",
        parse_mode=ParseMode.MARKDOWN
    )

    # 3) Запрашиваем стрим (await обязателен)
    stream = await openai_client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=history,
        stream=True
    )

    full_text = ""
    last_edit = time.monotonic()
    throttle_interval = 0.2  # минимум 200 мс между правками

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if not delta:
            continue
        full_text += delta

        now = time.monotonic()
        if now - last_edit >= throttle_interval:
            # Пытаемся отредактировать с Markdown
            try:
                await message.bot.edit_message_text(
                    text=full_text,
                    chat_id=chat_id,
                    message_id=sent.message_id,
                    parse_mode=ParseMode.MARKDOWN
                )
            except TelegramRetryAfter as e:
                # Если флад-контроль — ждём и пробуем снова в Markdown
                await asyncio.sleep(e.retry_after)
                await message.bot.edit_message_text(
                    text=full_text,
                    chat_id=chat_id,
                    message_id=sent.message_id,
                    parse_mode=ParseMode.MARKDOWN
                )
            except TelegramBadRequest as e:
                # Если проблема с парсингом Markdown — падаем в plain-text
                if "can't parse entities" in str(e):
                    await message.bot.edit_message_text(
                        text=full_text,
                        chat_id=chat_id,
                        message_id=sent.message_id,
                        parse_mode=None
                    )
                else:
                    raise
            last_edit = time.monotonic()

    # 4) Финальный flush
    if full_text:
        try:
            await message.bot.edit_message_text(
                text=full_text,
                chat_id=chat_id,
                message_id=sent.message_id,
                parse_mode=ParseMode.MARKDOWN
            )
        except TelegramBadRequest as e:
            if "can't parse entities" in str(e):
                await message.bot.edit_message_text(
                    text=full_text,
                    chat_id=chat_id,
                    message_id=sent.message_id,
                    parse_mode=None
                )
            else:
                raise

    # 5) Сохраняем ответ ассистента
    history.append({"role": "assistant", "content": full_text})


@router.message(F.photo, F.chat.type == "private")
async def photo_handler(message: Message):
    images = []
    for photo in message.photo:
        file = await message.bot.get_file(photo.file_id)
        image_stream = await message.bot.download_file(file.file_path)
        image_bytes = image_stream.read()
        encoded = base64.b64encode(image_bytes).decode('utf-8')
        images.append(encoded)

    comment = ""
    if message.caption is not None:
        comment = message.caption

    completion = openai_client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": comment},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{images[0]}",
                        },
                    },
                ],
            }
        ],
    )
    result = completion.choices[0].message.content
    await message.reply(text=result)

@router.message()
async def all_others(message: Message):
    print(message)