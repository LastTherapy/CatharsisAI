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


@router.message(F.text, F.chat.type == "private")
async def handle_chat(message: Message):
    bot = message.bot
    chat_id = message.chat.id
    history = chat_histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": message.text})

    sent = await message.reply("⏳")

    # Получаем Stream (без await)
    stream = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        stream=True
    )

    full_text = ""
    async for chunk in stream:
        # Берём прирост текста из атрибута content
        delta = chunk.choices[0].delta.content
        if delta is not None:
            full_text += delta
            await bot.edit_message_text(full_text, chat_id=chat_id, message_id=sent.message_id)

    history.append({"role": "assistant", "content": full_text})
