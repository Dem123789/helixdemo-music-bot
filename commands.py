from pyrogram import Client, filters
from pyrogram.types import Message


def register_command_handlers(
    app: Client,
    call,
    queues,
    current_track,
    paused_chats,
    muted_chats,
    loop_mode,
    autoplay_mode,
    get_queue,
    download_audio,
    MediaStream,
    log,
):

    # ========================================================
    # QUEUE
    # ========================================================

    @app.on_message(filters.command("queue"))
    async def queue_command(client: Client, message: Message):

        chat_id = message.chat.id
        queue = get_queue(chat_id)

        if chat_id not in current_track and not queue:
            await message.reply_text(
                "📭 **Queue is empty.**"
            )
            return

        text = "📋 **Music Queue**\n\n"

        if chat_id in current_track:

            current = current_track[chat_id]

            text += (
                "▶️ **Now Playing**\n"
                f"🎵 {current.get('title', 'Unknown')}\n\n"
            )

        if queue:

            text += "⏭ **Up Next**\n\n"

            for index, track in enumerate(
                queue,
                start=1,
            ):
                text += (
                    f"`{index}.` "
                    f"{track.get('title', 'Unknown')}\n"
                )

        else:

            text += (
                "📭 Queue ထဲမှာ "
                "နောက်ထပ်မရှိပါ။"
            )

        await message.reply_text(text)

    # ========================================================
    # PAUSE
    # ========================================================

    @app.on_message(filters.command("pause"))
    async def pause_command(client: Client, message: Message):

        chat_id = message.chat.id

        try:

            await call.pause(chat_id)

            paused_chats.add(chat_id)

            await message.reply_text(
                "⏸ **Music Paused**"
            )

        except Exception as e:

            log.exception("Pause error")

            await message.reply_text(
                "❌ **Pause မလုပ်နိုင်ပါ။**\n\n"
                f"`{str(e)[:500]}`"
            )

    # ========================================================
    # RESUME
    # ========================================================

    @app.on_message(filters.command("resume"))
    async def resume_command(client: Client, message: Message):

        chat_id = message.chat.id

        try:

            await call.resume(chat_id)

            paused_chats.discard(chat_id)

            await message.reply_text(
                "▶️ **Music Resumed**"
            )

        except Exception as e:

            log.exception("Resume error")

            await message.reply_text(
                "❌ **Resume မလုပ်နိုင်ပါ။**\n\n"
                f"`{str(e)[:500]}`"
            )

    # ========================================================
    # STOP
    # ========================================================

    @app.on_message(filters.command("stop"))
    async def stop_command(client: Client, message: Message):

        chat_id = message.chat.id

        try:

            await call.leave_call(chat_id)

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

    # ========================================================
    # SKIP
    # ========================================================

    @app.on_message(filters.command("skip"))
    async def skip_command(client: Client, message: Message):

        chat_id = message.chat.id
        queue = get_queue(chat_id)

        if not queue:

            await message.reply_text(
                "📭 Skip လုပ်စရာ queue မရှိပါ။"
            )

            return

        try:

            await call.leave_call(chat_id)

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
                f"🎵 {next_track.get('title', 'Unknown')}"
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

            await message.reply_text(
                "▶️ **Now Playing**\n\n"
                f"🎵 {next_track.get('title', 'Unknown')}"
            )

        except Exception as e:

            current_track.pop(
                chat_id,
                None,
            )

            log.exception("Skip error")

            await message.reply_text(
                "❌ **Next track မဖွင့်နိုင်ပါ။**\n\n"
                f"`{str(e)[:700]}`"
            )

    # ========================================================
    # LOOP
    # ========================================================

    @app.on_message(filters.command("loop"))
    async def loop_command(client: Client, message: Message):

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

    # ========================================================
    # AUTOPLAY
    # ========================================================

    @app.on_message(filters.command("autoplay"))
    async def autoplay_command(
        client: Client,
        message: Message,
    ):

        chat_id = message.chat.id

        if chat_id in autoplay_mode:

            autoplay_mode.discard(
                chat_id
            )

            await message.reply_text(
                "⛔ **Autoplay OFF**"
            )

        else:

            autoplay_mode.add(
                chat_id
            )

            await message.reply_text(
                "▶️ **Autoplay ON**"
            )

    # ========================================================
    # MUTE
    # ========================================================

    @app.on_message(filters.command("mute"))
    async def mute_command(
        client: Client,
        message: Message,
    ):

        chat_id = message.chat.id

        try:

            await call.mute(chat_id)

            muted_chats.add(
                chat_id
            )

            await message.reply_text(
                "🔇 **Muted**"
            )

        except Exception as e:

            log.exception("Mute error")

            await message.reply_text(
                "❌ **Mute မလုပ်နိုင်ပါ။**\n\n"
                f"`{str(e)[:500]}`"
            )

    # ========================================================
    # UNMUTE
    # ========================================================

    @app.on_message(filters.command("unmute"))
    async def unmute_command(
        client: Client,
        message: Message,
    ):

        chat_id = message.chat.id

        try:

            await call.unmute(chat_id)

            muted_chats.discard(
                chat_id
            )

            await message.reply_text(
                "🔊 **Unmuted**"
            )

        except Exception as e:

            log.exception("Unmute error")

            await message.reply_text(
                "❌ **Unmute မလုပ်နိုင်ပါ။**\n\n"
                f"`{str(e)[:500]}`"
            )
