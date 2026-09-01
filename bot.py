import os
import asyncio
import logging
from pathlib import Path

import yt_dlp

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream


# ============================================================
# CONFIG
# ============================================================

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_QUEUE = 50


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

log = logging.getLogger("music-bot")


# ============================================================
# TELEGRAM CLIENT
# ============================================================

app = Client(
    "telegram_music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


# ============================================================
# PYTGCALLS
# ============================================================

call = PyTgCalls(app)


# ============================================================
# DATA
# ============================================================

queues = {}

current_track = {}

paused_chats = set()

muted_chats = set()

loop_mode = {}

autoplay_mode = set()


# ============================================================
# QUEUE HELPERS
# ============================================================

def get_queue(chat_id):
    if chat_id not in queues:
        queues[chat_id] = []

    return queues[chat_id]


def clear_queue(chat_id):
    queues[chat_id] = []


def add_queue(chat_id, track):
    queue = get_queue(chat_id)

    if len(queue) >= MAX_QUEUE:
        return False

    queue.append(track)

    return True


def remove_queue_item(chat_id, index):
    queue = get_queue(chat_id)

    if index < 0 or index >= len(queue):
        return None

  
    return queue.pop(index)
  # ============================================================
# YOUTUBE SEARCH
# ============================================================

async def search_youtube(query):
    """
    Search YouTube and return the first result.
    """

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": True,
        "default_search": "ytsearch1",
    }

    loop = asyncio.get_running_loop()

    def do_search():
        with yt_dlp.YoutubeDL(options) as ydl:
            data = ydl.extract_info(
                query,
                download=False,
            )

            if not data:
                return None

            if "entries" in data:
                entries = data.get("entries") or []

                if not entries:
                    return None

                return entries[0]

            return data

    return await loop.run_in_executor(
        None,
        do_search,
    )


# ============================================================
# DOWNLOAD AUDIO
# ============================================================

async def download_audio(url):
    """
    Download audio using yt-dlp.
    """

    options = {
        "format": "bestaudio/best",
        "outtmpl": str(
            DOWNLOAD_DIR / "%(id)s.%(ext)s"
        ),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    loop = asyncio.get_running_loop()

    def do_download():

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=True,
            )

            filename = ydl.prepare_filename(
                info
            )

            return filename, info

    return await loop.run_in_executor(
        None,
        do_download,
    )


# ============================================================
# HOME KEYBOARD
# ============================================================

def home_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎵 Music",
                    callback_data="music",
                ),
                InlineKeyboardButton(
                    "📋 Playlist",
                    callback_data="playlist",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⚙️ Commands",
                    callback_data="commands",
                ),
                InlineKeyboardButton(
                    "❓ Help",
                    callback_data="help",
                ),
            ],
            [
                InlineKeyboardButton(
                    "❌ Close",
                    callback_data="close",
                ),
            ],
        ]
    )


# ============================================================
# MUSIC KEYBOARD
# ============================================================

def music_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⏸ Pause",
                    callback_data="pause",
                ),
                InlineKeyboardButton(
                    "▶️ Resume",
                    callback_data="resume",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⏭ Skip",
                    callback_data="skip",
                ),
                InlineKeyboardButton(
                    "⏹ Stop",
                    callback_data="stop",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📋 Queue",
                    callback_data="queue",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🏠 Home",
                    callback_data="home",
                ),
            ],
        ]
   # ============================================================
# START
# ============================================================

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):

    text = (
        "🎵 **Telegram Music Bot**\n\n"
        "Welcome! 👋\n\n"
        "🎧 YouTube music ကို Voice Chat ထဲမှာ "
        "ဖွင့်နိုင်ပါတယ်။\n\n"
        "အောက်က Menu ကနေ ရွေးချယ်ပါ 👇"
    )

    await message.reply_text(
        text,
        reply_markup=home_keyboard(),
    )


# ============================================================
# HELP
# ============================================================

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):

    text = (
        "❓ **Music Bot Commands**\n\n"

        "🎵 **Music**\n"
        "/play <song>\n"
        "/vplay <video>\n"
        "/fplay <song>\n"
        "/fvplay <video>\n\n"

        "⏯ **Player**\n"
        "/pause\n"
        "/resume\n"
        "/skip\n"
        "/stop\n"
        "/queue\n\n"

        "🔁 **Playback**\n"
        "/loop <0-10>\n"
        "/autoplay\n"
        "/mute\n"
        "/unmute\n\n"

        "📋 **Playlist**\n"
        "/playlist\n"
    )

    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🏠 Home",
                        callback_data="home",
                    )
                ]
            ]
        ),
    )


# ============================================================
# PLAY
# ============================================================

@app.on_message(filters.command("play"))
async def play_command(client, message: Message):

    if len(message.command) < 2:

        await message.reply_text(
            "❌ **Usage**\n\n"
            "`/play song name`\n\n"
            "ဥပမာ:\n"
            "`/play Alan Walker Faded`"
        )

        return

    query = " ".join(message.command[1:])

    status = await message.reply_text(
        "🔍 **Searching...**\n\n"
        f"🎵 `{query}`"
    )

    try:

        result = await search_youtube(query)

        if not result:

            await status.edit_text(
                "❌ Music မတွေ့ပါ။"
            )

            return

        title = result.get(
            "title",
            query,
        )

        webpage_url = result.get(
            "webpage_url"
        )

        if not webpage_url:

            video_id = result.get("id")

            if video_id:
                webpage_url = (
                    f"https://www.youtube.com/watch?v={video_id}"
                )

        if not webpage_url:

            await status.edit_text(
                "❌ YouTube URL မရပါ။"
            )

            return

        requested_by = (
            message.from_user.mention
            if message.from_user
            else "Unknown"
        )

        track = {
            "title": title,
            "url": webpage_url,
            "requested_by": requested_by,
        }

        chat_id = message.chat.id

        queue = get_queue(chat_id)

        # ----------------------------------------------------
        # NO ACTIVE TRACK
        # ----------------------------------------------------

        if chat_id not in current_track:

            await status.edit_text(
                "⬇️ **Downloading...**\n\n"
                f"🎵 {title}"
            )

            filename, info = await download_audio(
                webpage_url
            )

            track["file"] = filename

            current_track[chat_id] = track

            await call.play(
                chat_id,
                MediaStream(filename),
            )

            await status.edit_text(
                "🎵 **Now Playing**\n\n"
                f"🎶 **{title}**\n\n"
                f"👤 Requested by: "
                f"{track['requested_by']}",
                reply_markup=music_keyboard(),
            )

        # ----------------------------------------------------
        # ADD TO QUEUE
        # ----------------------------------------------------

        else:

            if not add_queue(
                chat_id,
                track,
            ):

                await status.edit_text(
                    "❌ Queue ပြည့်နေပါပြီ။"
                )

                return

            position = len(
                get_queue(chat_id)
            )

            await status.edit_text(
                "📋 **Added to Queue**\n\n"
                f"🎵 {title}\n\n"
                f"📌 Position: #{position}"
            )

    except Exception as e:

        log.exception(
            "Play error"
        )

        await status.edit_text(
            "❌ **Play Error**\n\n"
            f"`{str(e)[:1000]}`"
        )


# ============================================================
# QUEUE
# ============================================================

@app.on_message(filters.command("queue"))
async def queue_command(client, message: Message):

    chat_id = message.chat.id

    queue = get_queue(chat_id)

    if (
        chat_id not in current_track
        and not queue
    ):

        await message.reply_text(
            "📭 **Queue is empty.**"
        )

        return

    text = "📋 **Music Queue**\n\n"

    if chat_id in current_track:

        current = current_track[chat_id]

        text += (
            "▶️ **Now Playing**\n"
            f"🎵 {current['title']}\n\n"
        )

    if queue:

        text += "⏭ **Up Next**\n\n"

        for index, track in enumerate(
            queue,
            start=1,
        ):

            text += (
                f"`{index}.` "
                f"{track['title']}\n"
            )

    else:

        text += (
            "📭 Queue ထဲမှာ "
            "နောက်ထပ်မရှိပါ။"
        )

    await message.reply_text(
        text,
        reply_markup=music_keyboard(),
    )


# ============================================================
# PAUSE
# ============================================================

@app.on_message(filters.command("pause"))
async def pause_command(client, message: Message):

    chat_id = message.chat.id

    try:

        await call.pause(chat_id)

        paused_chats.add(chat_id)

        await message.reply_text(
            "⏸ **Music Paused**"
        )

    except Exception as e:

        log.exception(
            "Pause error"
        )

        await message.reply_text(
            "❌ Pause မလုပ်နိုင်ပါ။\n\n"
            f"`{str(e)[:500]}`"
        )


# ============================================================
# RESUME
# ============================================================

@app.on_message(filters.command("resume"))
async def resume_command(client, message: Message):

    chat_id = message.chat.id

    try:

        await call.resume(chat_id)

        paused_chats.discard(
            chat_id
        )

        await message.reply_text(
            "▶️ **Music Resumed**"
        )

    except Exception as e:

        log.exception(
            "Resume error"
        )

        await message.reply_text(
            "❌ Resume မလုပ်နိုင်ပါ။\n\n"
            f"`{str(e)[:500]}`"
        )


# ============================================================
# STOP
# ============================================================

@app.on_message(filters.command("stop"))
async def stop_command(client, message: Message):

    chat_id = message.chat.id

    try:

        await call.leave_call(
            chat_id
        )

    except Exception:
        pass

    queues.pop(
        chat_id,
        None,
    )

    current_track.pop(
        chat_id,
        None,
    )

    paused_chats.discard(
        chat_id
    )

    loop_mode.pop(
        chat_id,
        None,
    )

    autoplay_mode.discard(
        chat_id
    )

    await message.reply_text(
        "⏹ **Music Stopped**\n\n"
        "Queue ကိုလည်း ရှင်းပြီးပါပြီ။"
    )


# ============================================================
# SKIP
# ============================================================

@app.on_message(filters.command("skip"))
async def skip_command(client, message: Message):

    chat_id = message.chat.id

    queue = get_queue(chat_id)

    if not queue:

        await message.reply_text(
            "📭 Skip လုပ်စရာ queue မရှိပါ။"
        )

        return

    try:

        await call.leave_call(
            chat_id
        )

    except Exception:
        pass

    current_track.pop(
        chat_id,
        None,
    )

    next_track = queue.pop(0)

    try:

        await message.reply_text(
            "⏭ **Skipping...**\n\n"
            f"🎵 {next_track['title']}"
        )

        filename, info = await download_audio(
            next_track["url"]
        )

        next_track["file"] = filename

        current_track[chat_id] = next_track

        await call.play(
            chat_id,
            MediaStream(filename),
        )

    except Exception as e:

        current_track.pop(
            chat_id,
            None,
        )

        log.exception(
            "Skip error"
        )

        await message.reply_text(
            "❌ Next track မဖွင့်နိုင်ပါ။\n\n"
            f"`{str(e)[:700]}`"
        )

# ============================================================
# LOOP
# ============================================================

@app.on_message(filters.command("loop"))
async def loop_command(client, message: Message):

    chat_id = message.chat.id

    if len(message.command) < 2:

        current = loop_mode.get(
            chat_id,
            0,
        )

        await message.reply_text(
            "🔁 **Loop Mode**\n\n"
            f"Current: `{current}`\n\n"
            "အသုံးပြုရန်:\n"
            "`/loop 0` = Off\n"
            "`/loop 1` = Repeat 1 time\n"
            "`/loop 10` = Repeat 10 times"
        )

        return

    try:

        value = int(
            message.command[1]
        )

        if value < 0 or value > 10:
            raise ValueError

        loop_mode[chat_id] = value

        await message.reply_text(
            f"🔁 **Loop set to `{value}`**"
        )

    except ValueError:

        await message.reply_text(
            "❌ `0` ကနေ `10` အတွင်းပဲ ထည့်ပါ။"
        )


# ============================================================
# AUTOPLAY
# ============================================================

@app.on_message(filters.command("autoplay"))
async def autoplay_command(client, message: Message):

    chat_id = message.chat.id

    if chat_id in autoplay_mode:

        autoplay_mode.discard(chat_id)

        await message.reply_text(
            "⛔ **Autoplay OFF**"
        )

    else:

        autoplay_mode.add(chat_id)

        await message.reply_text(
            "▶️ **Autoplay ON**"
        )


# ============================================================
# MUTE
# ============================================================

@app.on_message(filters.command("mute"))
async def mute_command(client, message: Message):

    chat_id = message.chat.id

    try:

        await call.mute(chat_id)

        muted_chats.add(chat_id)

        await message.reply_text(
            "🔇 **Muted**"
        )

    except Exception as e:

        log.exception("Mute error")

        await message.reply_text(
            "❌ Mute မလုပ်နိုင်ပါ။\n\n"
            f"`{str(e)[:500]}`"
        )


# ============================================================
# UNMUTE
# ============================================================

@app.on_message(filters.command("unmute"))
async def unmute_command(client, message: Message):

    chat_id = message.chat.id

    try:

        await call.unmute(chat_id)

        muted_chats.discard(chat_id)

        await message.reply_text(
            "🔊 **Unmuted**"
        )

    except Exception as e:

        log.exception("Unmute error")

        await message.reply_text(
            "❌ Unmute မလုပ်နိုင်ပါ။\n\n"
            f"`{str(e)[:500]}`"
        )


# ============================================================
# PLAYLIST
# ============================================================

@app.on_message(filters.command("playlist"))
async def playlist_command(client, message: Message):

    text = (
        "📋 **Playlist**\n\n"
        "Playlist Menu\n\n"
        "• Create Playlist\n"
        "• Add Track\n"
        "• Remove Track\n"
        "• Delete Playlist\n"
        "• My Playlists"
    )

    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🏠 Home",
                        callback_data="home",
                    )
                ]
            ]
        ),
    )


# ============================================================
# CALLBACK HANDLER
# ============================================================

@app.on_callback_query()
async def callback_handler(
    client,
    query: CallbackQuery,
):

    data = query.data
    chat_id = query.message.chat.id

    # --------------------------------------------------------
    # HOME
    # --------------------------------------------------------

    if data == "home":

        await query.message.edit_text(
            "🎵 **Telegram Music Bot**\n\n"
            "Welcome back! 👋\n\n"
            "Menu ကနေ ရွေးချယ်ပါ 👇",
            reply_markup=home_keyboard(),
        )


    # --------------------------------------------------------
    # MUSIC
    # --------------------------------------------------------

    elif data == "music":

        await query.message.edit_text(
            "🎵 **Music Menu**\n\n"
            "/play <song>\n"
            "/vplay <video>\n"
            "/fplay <song>\n"
            "/fvplay <video>\n\n"
            "/pause\n"
            "/resume\n"
            "/skip\n"
            "/stop\n"
            "/queue\n"
            "/mute\n"
            "/unmute\n\n"
            "/loop 0-10\n"
            "/autoplay",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="home",
                        )
                    ]
                ]
            ),
        )


    # --------------------------------------------------------
    # PLAYLIST
    # --------------------------------------------------------

    elif data == "playlist":

        await query.message.edit_text(
            "📋 **Playlist Menu**\n\n"
            "Playlist management ကို "
            "ဒီနေရာကနေ သွားနိုင်ပါတယ်။",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="home",
                        )
                    ]
                ]
            ),
        )


    # --------------------------------------------------------
    # COMMANDS
    # --------------------------------------------------------

    elif data == "commands":

        await query.message.edit_text(
            "⚙️ **Commands**\n\n"
            "/start\n"
            "/help\n"
            "/play\n"
            "/vplay\n"
            "/fplay\n"
            "/fvplay\n"
            "/pause\n"
            "/resume\n"
            "/skip\n"
            "/stop\n"
            "/queue\n"
            "/loop\n"
            "/autoplay\n"
            "/mute\n"
            "/unmute\n"
            "/playlist",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="home",
                        )
                    ]
                ]
            ),
        )


    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    elif data == "help":

        await query.message.edit_text(
            "❓ **Help**\n\n"
            "Group Voice Chat ထဲမှာ music "
            "ဖွင့်ရန် `/play song name` ကိုသုံးပါ။\n\n"
            "ဥပမာ:\n"
            "`/play Alan Walker Faded`",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="home",
                        )
                    ]
                ]
            ),
        )


    # --------------------------------------------------------
    # PAUSE
    # --------------------------------------------------------

    elif data == "pause":

        try:

            await call.pause(chat_id)

            paused_chats.add(chat_id)

            await query.answer(
                "⏸ Paused"
            )

        except Exception as e:

            await query.answer(
                f"Error: {str(e)[:100]}",
                show_alert=True,
            )


    # --------------------------------------------------------
    # RESUME
    # --------------------------------------------------------

    elif data == "resume":

        try:

            await call.resume(chat_id)

            paused_chats.discard(chat_id)

            await query.answer(
                "▶️ Resumed"
            )

        except Exception as e:

            await query.answer(
                f"Error: {str(e)[:100]}",
                show_alert=True,
            )


    # --------------------------------------------------------
    # SKIP
    # --------------------------------------------------------

    elif data == "skip":

        await query.answer(
            "⏭ Please use /skip"
        )


    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    elif data == "stop":

        try:

            await call.leave_call(
                chat_id
            )

        except Exception:
            pass

        queues.pop(
            chat_id,
            None,
        )

        current_track.pop(
            chat_id,
            None,
        )

        paused_chats.discard(
            chat_id
        )

        loop_mode.pop(
            chat_id,
            None,
        )

        autoplay_mode.discard(
            chat_id
        )

        await query.answer(
            "⏹ Stopped"
        )


    # --------------------------------------------------------
    # QUEUE
    # --------------------------------------------------------

    elif data == "queue":

        queue = get_queue(chat_id)

        if not queue:

            await query.answer(
                "📭 Queue empty",
                show_alert=True,
            )

        else:

            text = "📋 **Queue**\n\n"

            for index, track in enumerate(
                queue,
                start=1,
            ):

                text += (
                    f"`{index}.` "
                    f"{track['title']}\n"
                )

            await query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🏠 Home",
                                callback_data="home",
                            )
                        ]
                    ]
                ),
            )


    # --------------------------------------------------------
    # CLOSE
    # --------------------------------------------------------

    elif data == "close":

        try:
            await query.message.delete()
        except Exception:
            pass


    # --------------------------------------------------------
    # ANSWER CALLBACK
    # --------------------------------------------------------

    try:
        await query.answer()
    except Exception:
        pass


# ============================================================
# MAIN
# ============================================================

async def main():

    log.info(
        "Starting Telegram Music Bot..."
    )

    await app.start()

    log.info(
        "Telegram client started."
    )

    call.start()

    log.info(
        "PyTgCalls started."
    )

    await asyncio.Event().wait()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
          )
      
  
