import os
from aiogram import Router, F
from aiogram.types import Message
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
router: Router = Router()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# В памяти храним историю: {chat_id: [ {"role":"user"/"assistant","content":...}, ... ]}
chat_histories: dict[int, list[dict]] = {}


@router.message()
async def handle_chat(message: Message):
    bot = message.bot
    chat_id = message.chat.id
    # Получаем или создаём историю для чата
    history = chat_histories.setdefault(chat_id, [])
    # Добавляем запрос пользователя
    history.append({"role": "user", "content": message.text})  # Формат OpenAI :contentReference[oaicite:5]{index=5}

    # Создаём заготовку ответа (пустая строка) и отправляем её
    sent = await message.reply("⏳")  # Показываем индикатор ожидания

    # Запрашиваем OpenAI с streaming
    stream = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        stream=True  # Streaming режим :contentReference[oaicite:6]{index=6}
    )

    full_text = ""
    # Проходим по чанкам и редактируем сообщение
    async for chunk in stream:  # Асинхронный генератор чанков :contentReference[oaicite:7]{index=7}
        delta = chunk.choices[0].delta.get("content")
        if not delta:
            continue
        full_text += delta
        # Обновляем текст сообщения постепенно
        await bot.edit_message_text(
            text=full_text,
            chat_id=chat_id,
            message_id=sent.message_id
        )  # Метод edit_message_text :contentReference[oaicite:8]{index=8}

    # Сохраняем окончательный ответ в истории
    history.append({"role": "assistant", "content": full_text})