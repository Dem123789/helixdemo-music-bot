from pyrogram import Client, filters
from pyrogram.types import Message


def register_help_handler(app: Client):

    @app.on_message(filters.command("help"))
    async def help_command(client: Client, message: Message):

        text = (
            "🎵 **Kristine Music Bot — Help**\n\n"
            "🎧 **Music Commands**\n"
            "• `/play <song>` — Play a song\n"
            "• `/queue` — Show music queue\n"
            "• `/pause` — Pause playback\n"
            "• `/resume` — Resume playback\n"
            "• `/skip` — Skip current song\n"
            "• `/stop` — Stop playback\n\n"
            "🔊 **Voice Chat**\n"
            "Join a Telegram Voice Chat and use `/play` "
            "to start playing music.\n\n"
            "ℹ️ More features will be added."
        )

        await message.reply_text(text)
