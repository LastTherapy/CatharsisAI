import os
from aiogram import Router, F
from aiogram.types import Message
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
router: Router = Router()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# In-memory chat histories: { chat_id: [ {"role":"user"/"assistant", "content":...}, ... ] }
chat_histories: dict[int, list[dict]] = {}


@router.message(F.text, F.chat.type == "private")
async def handle_chat(message: Message):
    bot = message.bot
    chat_id = message.chat.id

    # 1) Append user message to history
    history = chat_histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": message.text})

    # 2) Send a placeholder reply (we'll edit this)
    sent = await message.reply("⏳ thinking...")

    # 3) Call OpenAI with stream=True — await to get the async iterator
    stream = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        stream=True
    )

    # 4) Iterate over chunks and edit the same message
    full_text = ""
    async for chunk in stream:
        # chunk.choices[0].delta.content holds the incremental text
        delta = chunk.choices[0].delta.content
        if delta:
            full_text += delta
            await bot.edit_message_text(
                text=full_text,
                chat_id=chat_id,
                message_id=sent.message_id
            )

    # 5) Save assistant’s reply to history
    history.append({"role": "assistant", "content": full_text})