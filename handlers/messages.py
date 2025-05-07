import os
from aiogram import Router, F
from aiogram.types import Message
from openai import AsyncOpenAI
from dotenv import load_dotenv
from aiogram.exceptions import TelegramBadRequest
g
load_dotenv()
router: Router = Router()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# In-memory chat histories: { chat_id: [ {"role":"user"/"assistant", "content":...}, ... ] }
chat_histories: dict[int, list[dict]] = {}


@router.message(F.text, F.chat.type == "private")
async def handle_chat(message: Message):
    bot = message.bot
    chat_id = message.chat.id
    history = chat_histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": message.text})

    # send placeholder
    sent = await message.reply("⏳ thinking...")

    # await to get async iterator
    stream = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        stream=True
    )

    full_text = ""
    last_sent = ""  # track what we've already sent to Telegram

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if not delta:
            continue

        full_text += delta

        # only try edit if there's new content beyond what was last sent
        if full_text == last_sent:
            continue

        try:
            await message.bot.edit_message_text(
                text=full_text,
                chat_id=chat_id,
                message_id=sent.message_id
            )
            last_sent = full_text
        except TelegramBadRequest as e:
            # ignore "message is not modified" errors, re-raise others
            if "message is not modified" not in e.args[0]:
                raise

    history.append({"role": "assistant", "content": full_text})