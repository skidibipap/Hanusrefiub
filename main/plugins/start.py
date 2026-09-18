import asyncio
import os
from datetime import datetime, timedelta
from distutils.util import strtobool
from time import time

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from main.helper.keyboard import ikb, kb
from pyrogram.types import InlineKeyboardMarkup
from pytz import timezone

from main import ADMIN_IDS, AKSES_DEPLOY, BOT_ID, bot, fsub, logger
from main.database import DB, DB_PATH
from main.helper import (FILTERS, HANDLER, button_pas_pertama, decode, encode,
                         force_button, get_messages)

from .add_bot import cancel

START_TIME = datetime.utcnow()
START_TIME_ISO = START_TIME.replace(microsecond=0).isoformat()
TIME_DURATION_UNITS = (
    ("week", 60 * 60 * 24 * 7),
    ("day", 60**2 * 24),
    ("hour", 60**2),
    ("min", 60),
    ("sec", 1),
)


async def _human_time_duration(seconds):
    if seconds == 0:
        return "inf"
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append(f'{amount} {unit}{"" if amount == 1 else "s"}')
    return ", ".join(parts)


start_msg = """
<blockquote>👋 **Hallo, {}! Saya adalah {}!**

🤖 Saya dibuat untuk memudahkan kamu mengelola channel dengan fitur **Wajib Join** dan **Auto Post Konten** ke channel yang diinginkan secara otomatis!

❓ Atau, jika ada pertanyaan lebih lanjut, jangan ragu untuk menghubungi admin kami.

🙏 **Terima kasih dan selamat menggunakan layanan kami!**</blockquote>"""


def btn_start(message):
    if message.from_user.id in ADMIN_IDS:
        button = kb(
            [[("🚀 Deploy Fsub"), ("👥 Cek Bot")], ["💬 Contact Support"]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    else:
        button = kb(
            [["🚀 Deploy Fsub"], ["💬 Contact Support"]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    return button


pic_bg = "https://files.catbox.moe/ugslzl.jpg"


@HANDLER.BOTS("restore")
@HANDLER.ADMINS
async def restore(client, message):
    user_id = message.from_user.id
    msg_text = await client.ask(
        user_id,
        "<blockquote><b>Silahkan kirim document file .db!! Dan pastikan nama DB_NAME sesuai dengan config.py</b></blockquote>",
        filters=filters.document,
    )
    document = msg_text.document
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    await client.download_media(document, "./")
    return await message.reply(
        f"<blockquote><b>Sukses melakukan restore database, Silahkan ketik /reboot</blockquote></b>"
    )


@HANDLER.FSUB("setmsg")
@HANDLER.EXPIRED
async def setmsg(client, message):
    user_id = message.from_user.id
    owner = DB.get_var(client.me.id, "OWNER")
    adm = DB.get_list_from_var(client.me.id, "ADMINS")
    if message.from_user.id not in adm and message.from_user.id != owner:
        return
    msg_text = await client.ask(
        user_id,
        "<blockquote><b>Silahkan kirim text untuk dijadikan pesan wajib join.</b></blockquote>",
        filters=filters.text,
    )
    if await cancel(message, msg_text.text):
        return
    DB.set_var(client.me.id, "MSG_JOIN", msg_text.text)
    return await message.reply(
        f"<blockquote><b>Pesan wajib join diatur ke:\n\n{msg_text.text}</blockquote></b>"
    )


async def post_to_konten(client, message, link):
    try:
        if message.text:
            return
        media = message.video or message.photo
        caption = f"{message.caption or ''}\n\n{link}\n\n<blockquote><b>Auto Post By Bot: {bot.me.mention}</blockquote></b>"
        bahan = DB.get_var(client.me.id, "PIC_KONTEN")
        if bahan is not None:
            pic_dia = f"{message.id}_.jpg"
            await client.bash(f"wget {bahan} -O {pic_dia}")
            thumbnail = pic_dia
        elif bahan is None:
            pc = f"{message.id}_.jpg"
            await client.bash(f"wget {pic_bg} -O {pc}")
            thumbnail = pc
        else:
            thumbnail = await client.download_media(media.thumbs[-1].file_id)
        ch_konten = DB.get_list_from_var(client.me.id, "KONTEN")
        try:
            for ch in ch_konten:
                try:
                    return await client.send_photo(ch, thumbnail, caption=caption)
                except FloodWait as er:
                    await asyncio.sleep(er.value)
                    return await client.send_photo(ch, thumbnail, caption=caption)
        except Exception as er:
            logger.error(f"Error auto post {str(er)}")
    except Exception as er:
        logger.error(f"Error auto post: {str(er)}")


@HANDLER.BOTS("start", FILTERS.PRIVATE)
@HANDLER.BOT_BROADCAST
async def start_bot(client, message):
    return await message.reply(
        start_msg.format(message.from_user.mention, client.me.mention),
        reply_markup=btn_start(message),
    )


@HANDLER.CALLBACK_BOT("^first_start")
async def first_start(client, message):
    return await message.message.edit(
        start_msg.format(message.from_user.mention, client.me.mention),
        reply_markup=btn_start(message),
    )


@HANDLER.FSUB("start", FILTERS.PRIVATE_FSUB)
@HANDLER.FSUB_BROADCAST
@HANDLER.EXPIRED
async def _(client, message):
    kk = DB.get_var(client.me.id, "PROTECT")
    kon = strtobool(kk)
    chg = DB.get_var(client.me.id, "CH_BASE")
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except Exception:
            return
        string = await decode(base64_string)
        argument = string.split("-")
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(chg))
                end = int(int(argument[2]) / abs(chg))
            except BaseException:
                return
            if start <= end:
                ids = range(start, end + 1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
            temp_msg = await message.reply("__Tunggu Sebentar...__")
            try:
                mes = await get_messages(client, ids)
            except Exception as er:
                await message.reply(f"**Telah Terjadi Error **🥺\n{str(er)}")
                return
            await temp_msg.delete()
            for msg in mes:
                caption = msg.caption if msg.caption else ""
                try:
                    await msg.copy(
                        message.chat.id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        protect_content=kon,
                        reply_markup=None,
                    )
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    await msg.copy(
                        message.chat.id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        protect_content=kon,
                        reply_markup=None,
                    )
                except BaseException:
                    pass
        elif len(argument) == 2:
            try:
                ids = int(int(argument[1]) / abs(chg))
            except BaseException:
                return
            temp_msg = await message.reply("__Tunggu Sebentar...__")
            try:
                mes = await client.get_messages(chg, ids)
            except Exception as er:
                await message.reply(f"**Telah Terjadi Error **🥺\n{str(er)}")
                return
            caption = mes.caption if mes.caption else ""
            await temp_msg.delete()
            await mes.copy(
                message.chat.id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                protect_content=kon,
                reply_markup=None,
            )
    else:
        buttons = await button_pas_pertama(client, message)
        costum_text = DB.get_var(client.me.id, "MSG_JOIN")
        if costum_text:
            return await message.reply(
                f"<blockquote>👋 **Hello {message.from_user.mention}**\n\n**{costum_text}**</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        else:
            return await message.reply(
                f"<blockquote>👋 **Hello {message.from_user.mention}**\n\n**Saya dapat menyimpan file pribadi di Channel Tertentu dan pengguna lain dapat mengaksesnya dari link khusus.**</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons),
            )


@HANDLER.FSUB("start")
@HANDLER.FSUB_BROADCAST
@HANDLER.EXPIRED
async def start_bots(client, message):

    buttons = await force_button(client, message)
    costum_text = DB.get_var(client.me.id, "MSG_JOIN")
    try:
        if costum_text:
            return await message.reply(
                f"<blockquote>👋 **Hello {message.from_user.mention}**\n\n**{costum_text}**</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        else:
            return await message.reply(
                f"<blockquote>👋 **Hello {message.from_user.mention}\n\nAnda harus bergabung di Channel/Grup saya Terlebih dahulu untuk Melihat File yang saya Bagikan\n\nSilakan Join Ke Channel & Group Terlebih Dahulu**</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons),
            )

    except Exception as er:
        await message.reply(f"**Telah Terjadi Error **🥺\n{str(er)}")
        return


@HANDLER.BOTS("help", FILTERS.PRIVATE)
@HANDLER.ADMINS
async def _(client, message):
    msg = f"""
<b><blockquote>/buser - --Mengecek pengguna Bot {client.me.mention}--
/broadcast [balas pesan] - --Kirim pesan siaran ke-- pengguna bot {client.me.mention}
/restore - --Restore database--
/addexpired [id bot] [hari] - --Atur masa aktif bot--
/addseller [id pengguna] - --Menambahkan seller--
/addexpired [id bot] [hari] - --Atur masa aktif bot--
/delseller [id pengguna] - --Menghapus seller--
/getseller [id pengguna] - --Melihat seller--
/gban [id pengguna] - --Blokir pengguna--
/ungban [id pengguna] - --Buka blokir pengguna--
/gbanlist - --List pengguna diblokir--
/trash [balas pesan] - --Dump--
/reboot  - --Restart Bot--
/update  - --Update userbot--
/eval [berikan pesan] - --Execute kode--
/sh [berikan pesan] - --Jalankan perintah shell--
/info [id pengguna] - --Cek status bot fsub--
/ping - --Cek ping bot--
/uptime - --Cek waktu bot--
/limitbutton [id bot] [jumlah] - --Atur batas button bot--
/limitkonten [id bot] [jumlah] - --Atur batas Channel konten--</blockquote></b>"""
    btn = ikb([[("❌ Tutup", "closed")]])
    return await message.reply(msg, reply_markup=btn)


@HANDLER.FSUB("help")
@HANDLER.EXPIRED
async def helper_text(client, message):
    msg = f"""
<b><blockquote>/users - --Mengecek pengguna Bot {client.me.mention}--
/broadcast [balas pesan] - --Kirim pesan siaran ke-- pengguna bot {client.me.mention}
/addadmin [id pengguna] - --Menambahkan admin--
/deladmin [id pengguna] - --Menghapus admin--
/getadmin [id pengguna] - --Melihat admin--
/info - --Cek status bot fsub--
/ping - --Cek ping bot--
/uptime - --Cek waktu bot--
/addbutton [id grup/channel] - --Tambah button bot--
/delbutton [id grup/channel] - --Hapus button bot--
/getbutton - --Cek button bot--
/addkonten [id channel] - --Tambah channel auto konten--
/delkonten [id channel] - --Hapus channel auto konten--
/getkonten - --Cek button bot--
/limitbutton - --Cek limit button bot--
/limitkonten - --Cek limit channel auto konten--
/protect [True/False] - --Batasi konten dibot--
/setdb [id grup/channel] - --Atur database bot--
/getdb  - --Cek database bot--
/setmsg - --Untuk mengatur pesan wajib join--
/batch - --Untuk membuat link lebih dari satu file--
/genlink - --Buat tautan untuk satu posting--</blockquote></b>"""
    btn = ikb([[("❌ Tutup", "closed")]])
    return await message.reply(msg, reply_markup=btn)


# @HANDLER.POST_CHANNEL()
async def post_channel(client, message):
    dbc = DB.get_var(client.me.id, "CH_BASE")
    if message.chat.id != dbc:
        return
    converted_id = message.id * abs(dbc)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.me.username}?start={base64_string}"
    reply_markup = ikb(
        [[("🔄 Bagikan Tautan", f"https://telegram.me/share/url?url={link}", "url")]]
    )
    try:
        return await message.edit_reply_markup(reply_markup)
    except Exception:
        pass


@HANDLER.POST_PRIVATE()
@HANDLER.EXPIRED
async def up_bokep(client, message):
    owner = DB.get_var(client.me.id, "OWNER")
    adm = DB.get_list_from_var(client.me.id, "ADMINS")
    dbc = DB.get_var(client.me.id, "CH_BASE")
    if message.from_user.id not in adm and message.from_user.id != owner:
        return
    ppk = await message.reply("Tunggu sebentar...")
    iya = await message.copy(dbc)
    sagne = iya.id * abs(dbc)
    string = f"get-{sagne}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.me.username}?start={base64_string}"
    reply_markup = ikb(
        [[("🔄 Bagikan Tautan", f"https://telegram.me/share/url?url={link}", "url")]]
    )
    if DB.get_list_from_var(client.me.id, "KONTEN") is not None:
        await post_to_konten(client, message, link)
    await ppk.edit(
        f"<blockquote>**🖇️ Link Sharing File Berhasil Di Buat :**\n\n{link}\n\nSilahkan Cek Channel Konten Kamu</blockquote>",
        reply_markup=reply_markup,
    )
    try:
        return await iya.edit_reply_markup(reply_markup)
    except Exception:
        pass


@HANDLER.BOTS("delbot")
@HANDLER.ADMINS
async def del_users(client, message):
    if len(message.command) < 2:
        return await message.reply("Balas pesan pengguna atau berikan id bot.")
    ids = message.command[1]
    DB.remove_ubot(str(ids))
    DB.rm_all(int(ids))
    os.system(f"rm -rf {ids}*")
    return await message.reply(f"Hapus data untuk id {ids}")


@HANDLER.FSUB("setdb", FILTERS.PRIVATE)
@HANDLER.EXPIRED
async def setdb(client, message):
    owner = DB.get_var(client.me.id, "OWNER")
    if message.from_user.id != owner:
        return
    if len(message.command) < 2:
        return await message.reply(
            "Berikan id channel database\ncontoh : /setdb -100123456789"
        )
    ids = int(message.command[1])
    try:
        link = await client.export_chat_invite_link(ids)
        DB.set_var(client.me.id, "CH_BASE", ids)
        return await message.reply(f"Channel database berhasil di set `{ids}`\n{link}")
    except:
        return await message.reply(f"Maaf saya bukan admin di `{ids}`")


@HANDLER.FSUB("getdb", FILTERS.PRIVATE)
@HANDLER.EXPIRED
async def getdb(client, message):
    owner = DB.get_var(client.me.id, "OWNER")
    if message.from_user.id != owner:
        return
    try:
        ids = DB.get_var(client.me.id, "CH_BASE")
        link = await client.export_chat_invite_link(int(ids))
        return await message.reply(f"Channel database adalah `{ids}`\n{link}")
    except Exception as er:
        return await message.reply(f"Error: `{str(er)}`")


@HANDLER.BOTS("addprem")
@HANDLER.SELLER
async def member_prem(client, message):
    if len(message.command) < 2:
        return await message.reply(
            "Balas pesan pengguna atau berikan user_id.\ncontoh : /addprem 607067484"
        )
    ids = message.command[1]
    if int(ids) not in AKSES_DEPLOY:
        AKSES_DEPLOY.append(int(ids))
        return await message.reply(f"{ids} Berhasil di berikan akses deploy!!")
    else:
        return await message.reply(f"Maaf {ids} sudah mempunyai akses deploy")


@HANDLER.BOTS("addexpired")
@HANDLER.SELLER
async def add_aktif_bot(client, message):
    if len(message.command) < 3:
        return await message.reply(
            "Berikan id bot dengan jumlah hari\ncontoh : /addexpired 607067484 30"
        )
    ids = message.command[1]
    get_day = message.command[2]
    min2h = DB.get_list_from_var(BOT_ID, "FSUB_EXPIRED_H")
    list_done = DB.get_list_from_var(BOT_ID, "FSUB_EXPIRED")
    if int(ids) in min2h:
        DB.remove_from_var(BOT_ID, "FSUB_EXPIRED_H", int(ids))
    if int(ids) in list_done:
        DB.remove_from_var(BOT_ID, "FSUB_EXPIRED", int(ids))
    now = datetime.now(timezone("Asia/Jakarta"))
    expire_date = now + timedelta(days=int(get_day))
    DB.set_expired_date(int(ids), expire_date)
    return await message.reply(f"{ids} telah diaktifkan selama {get_day} hari.")


@HANDLER.BOTS("getprem")
@HANDLER.SELLER
async def cek_member_prem(client, message):
    msg = "**Daftar Pengguna Memiliki Akses Deploy**\n\n"
    for num, ex in enumerate(AKSES_DEPLOY, 1):
        try:
            afa = f"{num}, `{ex}`\n"
        except Exception:
            continue
        msg += afa
    return await message.reply(msg)


@HANDLER.BOTS("ping")
@HANDLER.FSUB("ping")
async def ping_pong(client, message):
    start = time()
    current_time = datetime.utcnow()
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime = await _human_time_duration(int(uptime_sec))
    m_reply = await message.reply("Pinging...")
    delta_ping = time() - start
    return await m_reply.edit(
        "**PONG!!**🏓 \n"
        f"**• Ping -** `{delta_ping * 1000:.3f}ms`\n"
        f"**• Uptime -** `{uptime}`\n"
    )


@HANDLER.BOTS("uptime")
@HANDLER.FSUB("uptime")
async def get_uptime(client, message):
    current_time = datetime.utcnow()
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime = await _human_time_duration(int(uptime_sec))
    return await message.reply_text(
        "🤖 **Bot Status:**\n"
        f"• **Uptime:** `{uptime}`\n"
        f"• **Start Time:** `{START_TIME_ISO}`"
    )


@HANDLER.BOTS("limitbutton")
@HANDLER.SELLER
async def add_max_bot(client, message):
    if len(message.command) < 3:
        return await message.reply(
            "Berikan id bot serta jumlah button.\nContoh: /limitbutton 20731464 2"
        )
    ids = message.command[1]
    getbt = message.command[2]
    DB.set_var(int(ids), "MAX_SUB", getbt)
    return await message.reply(f"**Bot** : {ids}\n**Buttons** : {getbt}")


@HANDLER.BOTS("limitkonten")
@HANDLER.SELLER
async def add_max_bot(client, message):
    if len(message.command) < 3:
        return await message.reply(
            "Berikan id bot serta jumlah konten.\nContoh: /limitkonten 20731464 2"
        )
    ids = message.command[1]
    getbt = message.command[2]
    DB.set_var(int(ids), "MAX_KONTEN", getbt)
    return await message.reply(f"**Bot** : {ids}\n**Konten** : {getbt}")


@HANDLER.BOTS("info")
@HANDLER.SELLER
async def _(client, message):
    if len(message.command) < 2:
        return await message.reply("Berikan id bot.\nContoh: /info 20731464")
    get_id = int(message.command[1])
    if get_id not in fsub._bot_id:
        return await message.reply(f"Tidak ada id bot {get_id} didatabase!!")
    expired_date = DB.get_expired_date(get_id)
    if expired_date:
        expir = expired_date.astimezone(timezone("Asia/Jakarta")).strftime(
            "%Y-%m-%d %H:%M"
        )
    else:
        expir = "Habis"
    data = DB.get_userdata(get_id)
    full = data["full"]
    username = data["username"]
    owner = DB.get_var(get_id, "OWNER")
    max_sub = DB.get_var(get_id, "MAX_SUB")
    max_konten = DB.get_var(get_id, "MAX_KONTEN")
    chbase = DB.get_var(get_id, "CH_BASE")
    admins = DB.get_list_from_var(get_id, "ADMINS")
    forsub = DB.get_list_from_var(get_id, "FORCE_SUB")
    konten = DB.get_list_from_var(get_id, "KONTEN")
    protek = DB.get_var(get_id, "PROTECT")
    pickn = DB.get_var(get_id, "PIC_KONTEN")
    msg = f"""
<b><blockquote>Data Bot <a href=https://t.me/{username}>{full}</a>
Owner: `{owner}`
Max Button: `{max_sub}`
Max Auto Post: `{max_konten}`
Channel Database: `{chbase}`
Total Admins: `{len(admins)}`
Total Button: `{len(forsub)}`
Total Channel Auto Post Konten: `{len(konten)}`
Default Gambar Konten: `{pickn}`
Protect Konten: {protek}
Masa Aktif: `{expir}`</blockquote></b>"""
    return await message.reply(msg, disable_web_page_preview=True)


@HANDLER.FSUB("info")
async def _(client, message):
    owner = DB.get_var(client.me.id, "OWNER")
    adm = DB.get_list_from_var(client.me.id, "ADMINS")
    if message.from_user.id not in adm and message.from_user.id != owner:
        return
    expired_date = DB.get_expired_date(client.me.id)
    if expired_date:
        expir = expired_date.astimezone(timezone("Asia/Jakarta")).strftime(
            "%Y-%m-%d %H:%M"
        )
    else:
        expir = "Habis"
    data = DB.get_userdata(client.me.id)
    full = data["full"]
    username = data["username"]
    owner = DB.get_var(client.me.id, "OWNER")
    max_sub = DB.get_var(client.me.id, "MAX_SUB")
    max_konten = DB.get_var(client.me.id, "MAX_KONTEN")
    chbase = DB.get_var(client.me.id, "CH_BASE")
    admins = DB.get_list_from_var(client.me.id, "ADMINS")
    forsub = DB.get_list_from_var(client.me.id, "FORCE_SUB")
    konten = DB.get_list_from_var(client.me.id, "KONTEN")
    protek = DB.get_var(client.me.id, "PROTECT")
    pickn = DB.get_var(client.me.id, "PIC_KONTEN")

    msg = f"""
<b><blockquote>Data Bot <a href=https://t.me/{username}>{full}</a>
Owner: `{owner}`
Max Button: `{max_sub}`
Max Auto Post: `{max_konten}`
Channel Database: `{chbase}`
Total Admins: `{len(admins)}`
Total Button: `{len(forsub)}`
Total Channel Auto Post Konten: `{len(konten)}`
Default Gambar Konten: `{pickn}`
Protect Konten: {protek}
Masa Aktif: `{expir}`</blockquote></b>"""
    return await message.reply(msg, disable_web_page_preview=True)


def USERBOT(count):
    expired_date = DB.get_expired_date(fsub._bot[int(count)].me.id)
    if expired_date:
        expir = expired_date.astimezone(timezone("Asia/Jakarta")).strftime(
            "%Y-%m-%d %H:%M"
        )
    else:
        expir = "Habis"
    K = DB.get_userdata(fsub._bot[int(count)].me.id)
    username = K["username"]
    full = K["full"]
    akun = f"<a href=https://t.me/{username}>{full}</a>"
    return f"""
<b>❏ Fsub To</b> <code>{int(count) + 1}/{len(fsub._bot)}</code>
<b> ├ Bot: {akun} </b>
<b> ├ ID:</b> <code>{fsub._bot[int(count)].me.id}</code>
<b> ╰ Expired</b> <code>{expir}</code>
"""


def get_remaining_days(expired_date):
    now = datetime.now(expired_date.tzinfo)
    time_diff = expired_date - now
    return max(0, time_diff.days + 1)


def userbot(user_id, count):
    button = ikb(
        [
            [("Hapus Bot", f"del_ubot {int(user_id)}")],
            [("Tambah Hari", f"add_expir {int(user_id)}")],
            [("Hapus Masa Aktif", f"del_expired {int(user_id)}")],
            [("❮", f"prev_ub {int(count)}"), ("❯", f"next_ub {int(count)}")],
            [("Tutup", f"closed")],
        ]
    )
    return button


@HANDLER.CALLBACK_BOT("^add_expir")
async def f(client, cq):
    user_id = cq.from_user.id
    if user_id not in ADMIN_IDS:
        return await cq.answer(
            f"❌ Jangan Diklik Boss {cq.from_user.first_name} {cq.from_user.last_name or ''}",
            True,
        )
    await cq.message.delete()
    get_day = await client.ask(
        user_id, "**Silahkan masukkan jumlah hari!!**", filters=filters.text
    )
    hari = int(get_day.text)
    get_id = int(cq.data.split()[1])
    data = get_remaining_days(DB.get_expired_date(get_id))
    add = hari + int(data)
    now = datetime.now(timezone("Asia/Jakarta"))
    expire_date = now + timedelta(days=add)
    DB.set_expired_date(get_id, expire_date)
    return await client.send_message(
        user_id, f"Masa Aktif Bot {get_id} diatur menjadi {add} hari."
    )


@HANDLER.CALLBACK_BOT("^del_expired")
async def f(client, cq):
    user_id = cq.from_user.id
    if user_id not in ADMIN_IDS:
        return await cq.answer(
            f"❌ Jangan Diklik Boss {cq.from_user.first_name} {cq.from_user.last_name or ''}",
            True,
        )
    get_id = int(cq.data.split()[1])
    DB.rem_expired_date(get_id)
    return await cq.edit_message_text(f"Masa Aktif Bot {get_id} berhasil dihapus.")


@HANDLER.CALLBACK_BOT("^del_ubot")
async def f(client, cq):
    user_id = cq.from_user.id
    if user_id not in ADMIN_IDS:
        return await cq.answer(
            f"❌ Jangan Diklik Boss {cq.from_user.first_name} {cq.from_user.last_name or ''}",
            True,
        )
    get_id = int(cq.data.split()[1])
    data = DB.get_userdata(get_id)
    username = data["username"]
    full = data["full"]
    get_mention = f"<a href=https://t.me/{username}>{full}</a>"
    for X in fsub._bot:
        if get_id == X.me.id:
            DB.remove_ubot(X.me.id)
            DB.rm_all(X.me.id)
            DB.rem_expired_date(X.me.id)
            fsub._bot.remove(X)
            fsub._bot_id.remove(X.me.id)
            os.system(f"rm -rf {X.me.id}*")
            return await cq.edit_message_text(
                f"<b> ✅ {get_mention} Berhasil Di Hapus Dari Database</b>"
            )


@HANDLER.CALLBACK_BOT("^(prev_ub|next_ub)")
async def _(client, cq):
    query = cq.data.split()
    count = int(query[1])
    if query[0] == "next_ub":
        if count == len(fsub._bot) - 1:
            count = 0
        else:
            count += 1
    elif query[0] == "prev_ub":
        if count == 0:
            count = len(fsub._bot) - 1
        else:
            count -= 1
    return await cq.edit_message_text(
        USERBOT(count),
        reply_markup=userbot(fsub._bot[count].me.id, count),
        disable_web_page_preview=True,
    )


@HANDLER.REGEX_BOT("^👥 Cek Bot")
async def _(client, message):
    return await message.reply(
        USERBOT(0),
        reply_markup=userbot(fsub._bot[0].me.id, 0),
        disable_web_page_preview=True,
    )
