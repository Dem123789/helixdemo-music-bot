from pyrogram import Client, filters
from pyrogram.types import Message

from config import API_ID, API_HASH, BOT_TOKEN


def register_start_handler(app: Client):

    @app.on_message(filters.command("start"))
    async def start_command(client: Client, message: Message):

        user = message.from_user

        name = user.first_name if user else "User"

        text = (
            f"🎵 **Welcome {name}!**\n\n"
            "🎧 **Kristine Music Bot**\n\n"
            "I can play music in Telegram Voice Chats.\n\n"
            "🎶 Use `/play <song name>` to play music.\n"
            "📜 Use `/help` to see available commands."
        )

        await message.reply_text(text)
