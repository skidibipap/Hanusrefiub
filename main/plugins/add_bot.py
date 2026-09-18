import importlib
import os
from datetime import datetime

from dateutil.relativedelta import relativedelta
from pyrogram import filters
from main.helper.keyboard import ikb
from pyrogram.types import InlineKeyboardButton as Ikb
from pyrogram.types import InlineKeyboardMarkup, ReplyKeyboardRemove
from pytz import timezone

from main import (ADMIN_IDS, AKSES_DEPLOY, API_HASH, API_ID, BOT_ID, LOG_GRUP,
                  FsubBot, bot, fsub)
from main.database import DB
from main.helper import HANDLER, upload_media
from main.plugins import BOT_PLUGINS


async def cancel(message, text):
    if text.startswith("/"):
        await bot.send_message(
            message.from_user.id,
            "Proses di batalkan, silahkan coba lagi",
        )
        return True
    else:
        return False


async def setExpiredUser(user_id, _fsub):
    seles = DB.get_list_from_var(BOT_ID, "seller")
    if user_id in seles:
        now = datetime.now(timezone("Asia/Jakarta"))
        expired = now + relativedelta(months=12)
        DB.set_expired_date(_fsub, expired)
    else:
        now = datetime.now(timezone("Asia/Jakarta"))
        expired = now + relativedelta(months=1)
        DB.set_expired_date(_fsub, expired)


@HANDLER.FSUB("addpic")
@HANDLER.EXPIRED
async def _(client, message):
    owner = DB.get_var(client.me.id, "OWNER")
    adm = DB.get_list_from_var(client.me.id, "ADMINS")
    if message.from_user.id not in adm and message.from_user.id != owner:
        return
    bahan = await client.ask(
        message.from_user.id,
        "<b>Silahkan kirim gambar anda untuk diatur menjadi gambar konten.</b>",
        filters=filters.photo,
        reply_markup=ReplyKeyboardRemove(),
    )
    # if await cancel(message, bahan.text):
    # return
    bahan2 = await client.download_media(bahan)
    konten = await upload_media(bahan2)
    DB.set_var(client.me.id, "PIC_KONTEN", konten)
    return await message.reply(
        f"**Gambar konten anda diatur ke:\n{konten}", disable_web_page_preview=True
    )


@HANDLER.REGEX_BOT("^🚀 Deploy Fsub")
async def _(client, message):
    user_id = message.from_user.id
    min2h = DB.get_list_from_var(BOT_ID, "FSUB_EXPIRED_H")
    list_done = DB.get_list_from_var(BOT_ID, "FSUB_EXPIRED")
    if user_id not in AKSES_DEPLOY:
        return await message.reply(
            "<blockquote><b>Kamu belum memiliki akses untuk melakukan Deploy Fsub!!\nHubungi @Akwcuy untuk melakukan pembayaran dan dapatkan akses untuk melakukan Deploy Fsub.</b></blockquote>"
        )
    bot_token = await client.ask(
        user_id,
        "<b>Silahkan masukkan Bot token Anda</b>",
        filters=filters.text,
        reply_markup=ReplyKeyboardRemove(),
    )
    if await cancel(message, bot_token.text):
        return
    uy = await message.reply("<blockquote>Tunggu sebentar...</blockquote>")
    name_id = bot_token.text.split(":")[0]
    NB = FsubBot(
        name=str(name_id),
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=bot_token.text,
    )
    try:
        await uy.delete()
        await NB.start()
        await fsub.set_cmds_fsub(NB)
        if NB.me.id in min2h:
            DB.remove_from_var(BOT_ID, "FSUB_EXPIRED_H", NB.me.id)
        if NB.me.id in list_done:
            DB.remove_from_var(BOT_ID, "FSUB_EXPIRED", NB.me.id)
        await client.send_message(
            user_id,
            f"<blockquote><b>Bot Ditemukan:</b>\n<b>Nama :</b> {NB.me.mention}\n<b>ID :</b> {NB.me.id}\n<b>Username :</b> @{NB.me.username}</blockquote>",
        )
    except Exception as e:
        return await client.send_message(
            user_id, f"<blockquote>**ERROR**:\n{str(e)}</blockquote>"
        )
    channel_id = await client.ask(
        user_id,
        "<blockquote><b>Masukan ID Channel Untuk Database, Pastikan Bot sudah menjadi admin di Channel Database\nContoh -100xxxx</b></blockquote>",
        filters=filters.text,
    )
    if await cancel(message, channel_id.text):
        return
    try:
        await NB.export_chat_invite_link(int(channel_id.text))
        await channel_id.reply(
            f"<blockquote>Channel Database Ditemukan `{channel_id.text}`</blockquote>"
        )
    except Exception:
        channel_id = await client.ask(
            user_id,
            f"<blockquote>Pastikan @{NB.me.username} adalah admin di Channel Database tersebut.\n\n Channel Database : `{channel_id.text}`\n\nMohon Masukkan Ulang !</blockquote>",
            filters=filters.text,
        )
    sub_id = await client.ask(
        user_id,
        "<blockquote><b>Silakan Masukkan ID Channel Atau Grup Sebagai Force Subscribe !\n\nDan Pastikan Bot Anda Adalah Admin Di Grup/Channel Tersebut.</b></blockquote>",
    )
    if await cancel(message, sub_id.text):
        return
    try:
        if int(sub_id.text) != 0:
            await NB.export_chat_invite_link(int(sub_id.text))
            await sub_id.reply(
                f"<blockquote>Force-Subs terdeteksi `{sub_id.text}`</blockquote>"
            )
    except Exception:
        sub_id = await client.ask(
            user_id,
            f"<blockquote>Pastikan @{NB.me.username} adalah admin di Channel atau Group tersebut.\n\n Channel atau Group Saat Ini: `{sub_id.text}`\n\nMohon Masukkan Ulang !</blockquote>",
            filters=filters.text,
        )

    admin_id = await client.ask(
        user_id,
        "<blockquote><b>Silakan Masukan ID Admin Untuk Bot Anda !</b></blockquote>",
        filters=filters.text,
    )
    if await cancel(message, admin_id.text):
        return
    try:
        admin_ids = int(admin_id.text)
    except ValueError:
        admin_id = await client.ask(
            user_id,
            "<blockquote>Bukan ID Pengguna Yang Valid, ID Pengguna Haruslah Berupa Integer</blockquote>",
            filters=filters.text,
        )
    owner_id = await client.ask(
        user_id,
        "<blockquote><b>Silakan Masukan ID Owner Untuk Bot Anda !!</b></blockquote>",
        filters=filters.text,
    )
    if await cancel(message, owner_id.text):
        return
    try:
        owner_ids = int(owner_id.text)
    except ValueError:
        owner_id = await client.ask(
            user_id,
            "<blockquote>Bukan ID Pengguna Yang Valid, ID Pengguna Haruslah Berupa Integer</blockquote>",
            filters=filters.text,
        )
    await client.send_message(
        user_id,
        "<blockquote><b>Sukses Di Deploy . Silakan Tunggu Sebentar...</b></blockquote>",
    )
    DB.add_ubot(str(NB.me.id), API_ID, API_HASH, bot_token.text)
    DB.set_var(NB.me.id, "OWNER", owner_ids)
    DB.set_var(NB.me.id, "MAX_SUB", 3)
    DB.set_var(NB.me.id, "MAX_KONTEN", 3)
    DB.set_var(NB.me.id, "CH_BASE", int(channel_id.text))
    DB.add_to_var(NB.me.id, "ADMINS", admin_ids)
    DB.add_to_var(NB.me.id, "FORCE_SUB", int(sub_id.text))
    DB.set_var(NB.me.id, "PROTECT", "True")
    await setExpiredUser(user_id, NB.me.id)
    expired = DB.get_expired_date(NB.me.id)
    msg = await client.send_message(
        LOG_GRUP,
        f"<blockquote>**Nama** : {NB.me.first_name}\n**Username** : @{NB.me.username}\n**Id**: {NB.me.id}\n**Masa Aktif** : {expired}\n\n**Pembuat**: {message.from_user.mention}\n**Id Pengguna**: {message.from_user.id}</blockquote>",
    )
    await client.pin_chat_message(LOG_GRUP, msg.id)
    btn = ikb(
        [
            [
                (
                    "Bot Fsub Mu Aktif",
                    f"telah_aktif {message.from_user.id} {NB.me.username}",
                )
            ]
        ]
    )
    await client.send_message(
        LOG_GRUP, f"Pesan untuk deployer @{NB.me.username}", reply_markup=btn
    )
    os.system(f"rm -rf {name_id}*")

    for plus in BOT_PLUGINS:
        importlib.reload(importlib.import_module(f"main.plugins.{plus}"))
    return await client.send_message(
        user_id,
        "<blockquote>**Bot Fsub Anda Sudah Aktif Dan Bisa Langsung Digunakan !\n\nKetik /help Di Bot Anda Untuk Melihat Perintah Yang Tersedia .\n\nTerima Kasih ...**</blockquote>",
    )


@HANDLER.CALLBACK_BOT("^closed")
@HANDLER.CALLBACK_FSUB("^closed")
async def closed(_, cq):
    return await cq.message.delete()


@HANDLER.CALLBACK_BOT("^telah_aktif")
async def _(client, callback_query):
    user_ids = int(callback_query.data.split()[1])
    bot_user = callback_query.data.split()[2]
    await client.send_message(
        user_ids, f"✅ Bot kamu telah aktif silahkan start bot @{bot_user}"
    )
    return await callback_query.message.edit("**Pesan telah di kirim**")


@HANDLER.REGEX_BOT("^💬 Contact Support")
async def more_admins(client, message):
    new_msg = """
<b>Dibawah ini adalah Owner Saya. Kamu dapat menghubungi salah satu dari mereka.</b>"""
    tombol = []
    row = []
    for admin in ADMIN_IDS:
        try:
            user = await client.get_users(admin)
            owner_name = user.first_name
            row.append(Ikb(owner_name, user_id=f"{user.id}"))
            if len(row) == 2:
                tombol.append(row)
                row = []
        except Exception as e:
            return await message.reply(f"Error fetching user {admin}: {e}")
    if row:
        tombol.append(row)
    last_row = [
        Ikb(text="⬅️ Kembali", callback_data="first_start"),
        Ikb(text="❌ Tutup", callback_data="closed"),
    ]
    tombol.append(last_row)

    markup = InlineKeyboardMarkup(tombol)

    return await message.reply(new_msg, reply_markup=markup)
