from pyrogram import filters
from main.helper.keyboard import ikb

from main.database import DB
from main.helper import FILTERS, HANDLER, encode, get_message_id


@HANDLER.FSUB("batch", FILTERS.PRIVATE)
@HANDLER.EXPIRED
async def batch(client, message):
    owner = DB.get_var(client.me.id, "OWNER")
    adm = DB.get_list_from_var(client.me.id, "ADMINS")
    chg = DB.get_var(client.me.id, "CH_BASE")

    if message.from_user.id not in adm and message.from_user.id != owner:
        return
    while True:
        try:
            first_message = await client.ask(
                message.from_user.id,
                "<b>Silahkan Teruskan Pesan/File Pertama dari Channel Database. (Forward with Qoute)</b>\n\n<b>atau Kirim Link Postingan dari Channel Database</b>",
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
            )
        except BaseException:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        await first_message.reply(
            "❌ <b>ERROR</b>\n\n<b>Postingan yang Diforward ini bukan dari Channel Database saya</b>",
            quote=True,
        )
        continue

    while True:
        try:
            second_message = await client.ask(
                message.from_user.id,
                "<b>Silahkan Teruskan Pesan/File Terakhir dari Channel DataBase. (Forward with Qoute)</b>\n\n<b>atau Kirim Link Postingan dari Channel Database</b>",
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
            )
        except BaseException:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        await second_message.reply(
            "❌ <b>ERROR</b>\n\n<b>Postingan yang Diforward ini bukan dari Channel Database saya</b>",
            quote=True,
        )
        continue

    string = f"get-{f_msg_id * abs(chg)}-{s_msg_id * abs(chg)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.me.username}?start={base64_string}"
    btn = ikb(
        [[("Bagikan Tautan", f"https://telegram.me/share/url?url={link}", "url")]]
    )
    await second_message.reply_text(
        f"<b>Link Sharing File Berhasil Di Buat:</b>\n\n{link}",
        quote=True,
        reply_markup=btn,
    )


@HANDLER.FSUB("genlink", FILTERS.PRIVATE)
@HANDLER.EXPIRED
async def link_generator(client, message):
    owner = DB.get_var(client.me.id, "OWNER")
    adm = DB.get_list_from_var(client.me.id, "ADMINS")
    chg = DB.get_var(client.me.id, "CH_BASE")
    if message.from_user.id not in adm and message.from_user.id != owner:
        return
    while True:
        try:
            channel_message = await client.ask(
                message.from_user.id,
                "<b>Silahkan Teruskan Pesan dari Channel DataBase. (Forward with Qoute)</b>\n\n<b>atau Kirim Link Postingan dari Channel Database</b>",
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
            )
        except BaseException:
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        await channel_message.reply(
            "❌ <b>ERROR</b>\n\n<b>Postingan yang Diforward ini bukan dari Channel Database saya</b>",
            quote=True,
        )
        continue

    base64_string = await encode(f"get-{msg_id * abs(chg)}")
    link = f"https://t.me/{client.me.username}?start={base64_string}"
    btn = ikb(
        [[("Bagikan Tautan", f"https://telegram.me/share/url?url={link}", "url")]]
    )
    await channel_message.reply_text(
        f"<b>Link File Sharing Berhasil Di Buat:</b>\n\n{link}",
        quote=True,
        reply_markup=btn,
    )
