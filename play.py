from pyrogram import Client, filters
from pyrogram.types import Message


def register_play_handler(app: Client):

    @app.on_message(filters.command("play"))
    async def play_command(client: Client, message: Message):

        if len(message.command) < 2:
            await message.reply_text(
                "🎵 **အသုံးပြုပုံ**\n\n"
                "`/play <song name>`\n\n"
                "ဥပမာ — `/play Faded`"
            )
            return

        query = " ".join(message.command[1:])

        status = await message.reply_text(
            f"🔎 **ရှာဖွေနေပါတယ်...**\n\n"
            f"🎵 `{query}`"
        )

        # Music Core ကို နောက်အဆင့်မှာ ချိတ်ပေးမည်
        await status.edit_text(
            "🎧 **Music Core မချိတ်ရသေးပါ။**\n\n"
            f"🔎 Search Query: `{query}`\n\n"
            "⏳ Music search/player module ကို "
            "နောက်အဆင့်မှာ ချိတ်ပေးပါမယ်။"
        )
