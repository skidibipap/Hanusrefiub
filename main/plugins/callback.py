from pyrogram import filters
from main.helper.keyboard import ikb
from pyrogram.types import InlineKeyboardMarkup
from pytz import timezone

from main.database import DB
from main.helper import HANDLER, button_pas_pertama

from .add_bot import cancel


@HANDLER.CALLBACK_FSUB("^users_settings")
async def usettings(client, cq):
    button = ikb(
        [
            [("Admins", "set_admins"), ("F-Subs", "set_fsubs")],
            [("Costum Text", "set_text")],
            [("Close", "closed")],
        ]
    )
    msg = "**Silahkan pilih pengaturan yang ingin kamu atur.**"
    return await cq.edit_message_text(msg, reply_markup=button)


@HANDLER.CALLBACK_FSUB("^users_info")
async def uinfo(client, cq):
    user_id = cq.from_user.id
    owner = DB.get_var(client.me.id, "OWNER")
    adm = DB.get_list_from_var(client.me.id, "ADMINS")
    button = ikb(
        [
            [("Admins", "set_admins"), ("F-Subs", "set_fsubs")],
            [("Costum Text", "set_text")],
            [("Close", "closed")],
        ]
    )
    if user_id not in adm and user_id != owner:
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
    return await cq.edit_message_text(
        msg, disable_web_page_preview=True, reply_markup=button
    )


@HANDLER.CALLBACK_FSUB("^set_admins")
async def cb_admin(client, cq):
    owner = DB.get_var(client.me.id, "OWNER")
    keyb = ikb(
        [
            [("Add Admins", "add_admins"), ("Del Admins", "del_admins")],
            [("Back", "users_settings")],
            [("Close", "closed")],
        ]
    )
    if cq.from_user.id == int(owner):
        msg = "**Daftar Admin**\n\n"
        adm = DB.get_list_from_var(client.me.id, "ADMINS")
        if not adm:
            return await cq.edit_message_text(
                "Belum ada Admin yang terdaftar.", reply_markup=keyb
            )
        for num, ex in enumerate(adm, start=1):
            try:
                afa = f"{num}.`{ex}`\n"
            except Exception:
                continue
            msg += afa
        return await cq.edit_message_text(msg, reply_markup=keyb)


@HANDLER.CALLBACK_FSUB("^(add_admins|del_admins)")
async def etc_admins(client, cq):
    message = cq.message
    user_id = cq.from_user.id
    adm = DB.get_list_from_var(client.me.id, "ADMINS")
    keyb = ikb(
        [
            [("Add Admins", "add_admins"), ("Del Admins", "del_admins")],
            [("Back", "users_settings")],
            [("Close", "closed")],
        ]
    )
    query = cq.data.split()
    owner = DB.get_var(client.me.id, "OWNER")
    if user_id == int(owner):
        if query[0] == "add_admins":
            await cq.answer()
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
            admin_ids = int(admin_id.text)
            if admin_ids in adm:
                return await message.reply(
                    f"**`{admin_ids}` sudah ada didalam daftar admins.**",
                    reply_markup=keyb,
                )
            DB.add_to_var(client.me.id, "ADMINS", admin_ids)
            return await message.reply(
                f"**`{admin_ids}` Berhasil ditambahkan ke daftar admins.**",
                reply_markup=keyb,
            )

        elif query[0] == "del_admins":
            await cq.answer()
            admin_id = await client.ask(
                user_id,
                "<blockquote><b>Silakan Masukan ID Admin Untuk Dihapus dari Bot Anda !</b></blockquote>",
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
            admin_ids = int(admin_id.text)
            if admin_ids not in adm:
                return await message.reply(
                    f"**`{admin_ids}` tidak ada didalam daftar admins.**",
                    reply_markup=keyb,
                )
            DB.remove_from_var(client.me.id, "ADMINS", admin_ids)
            return await message.reply(
                f"**`{admin_ids}` Berhasil dihapus dari daftar admins.**",
                reply_markup=keyb,
            )


@HANDLER.CALLBACK_FSUB("^set_fsubs")
async def c_fsub(client, cq):
    owner = DB.get_var(client.me.id, "OWNER")
    keyb = ikb(
        [
            [("Add Button", "add_buttons"), ("Del Button", "del_buttons")],
            [("Back", "users_settings")],
            [("Close", "closed")],
        ]
    )
    if cq.from_user.id == int(owner):
        msg = "**List Fsub / Button**\n\n"
        adm = DB.get_list_from_var(client.me.id, "FORCE_SUB")
        if not adm:
            return await cq.edit_message_text("List Button Kosong", reply_markup=keyb)
        for num, ex in enumerate(adm, start=1):
            try:
                jj = await client.get_chat(ex)
                afa = f"{num}. `{jj.id}` | {jj.title}\n"
            except Exception:
                afa = f"{num}. `{ex}`\n"
            msg += afa
        return await cq.edit_message_text(msg, reply_markup=keyb)


@HANDLER.CALLBACK_FSUB("^(add_buttons|del_buttons)")
async def etc_button(client, cq):
    user_id = cq.from_user.id
    message = cq.message
    adm = DB.get_list_from_var(client.me.id, "FORCE_SUB")
    keyb = ikb(
        [
            [("Add Button", "add_buttons"), ("Del Button", "del_buttons")],
            [("Back", "users_settings")],
            [("Close", "closed")],
        ]
    )
    query = cq.data.split()
    owner = DB.get_var(client.me.id, "OWNER")
    if user_id == int(owner):
        if query[0] == "add_buttons":
            await cq.answer()
            sub_id = await client.ask(
                user_id,
                "<blockquote><b>Silakan Masukkan ID Channel Atau Grup Sebagai Force Subscribe !\n\nDan Pastikan Bot Anda Adalah Admin Di Grup/Channel Tersebut.</b></blockquote>",
            )
            if await cancel(message, sub_id.text):
                return
            try:
                if int(sub_id.text) != 0:
                    link = await client.export_chat_invite_link(int(sub_id.text))
                    await sub_id.reply(
                        f"<blockquote>Force-Subs terdeteksi `{sub_id.text}`\n{link}</blockquote>"
                    )
            except Exception:
                sub_id = await client.ask(
                    user_id,
                    f"<blockquote>Pastikan @{client.me.username} adalah admin di Channel atau Group tersebut.\n\n Channel atau Group Saat Ini: `{sub_id.text}`\n\nMohon Masukkan Ulang !</blockquote>",
                    filters=filters.text,
                )
            sub_ids = int(sub_id.text)
            link = await client.export_chat_invite_link(sub_ids)
            if sub_ids in adm:
                return await message.reply(
                    f"**`{sub_ids}` sudah ada didalam daftar F-Subs**.",
                    reply_markup=keyb,
                )
            DB.add_to_var(client.me.id, "FORCE_SUB", sub_ids)
            return await message.reply(
                f"**`{sub_ids}` Berhasil ditambahkan ke daftar F-Subs.\n{link}**",
                reply_markup=keyb,
            )

        elif query[0] == "del_buttons":
            await cq.answer()
            sub_id = await client.ask(
                user_id,
                "<blockquote><b>Silakan Masukkan ID Channel Atau Grup Force Subscribe Untuk Dihapus !!</b></blockquote>",
            )
            if await cancel(message, sub_id.text):
                return
            try:
                if int(sub_id.text) != 0:
                    await sub_id.reply(
                        f"<blockquote>Force-Subs terdeteksi `{sub_id.text}`</blockquote>"
                    )
            except Exception:
                sub_id = await client.ask(
                    user_id,
                    f"<blockquote>Sepertinya anda memasukkan id Channel/Group yang salah</blockquote>",
                    filters=filters.text,
                )
            sub_ids = int(sub_id.text)
            if sub_ids not in adm:
                return await message.reply(
                    f"**`{sub_ids}` tidak ada didalam daftar F-Subs**.",
                    reply_markup=keyb,
                )
            DB.remove_from_var(client.me.id, "FORCE_SUB", sub_ids)
            return await message.reply(
                f"**`{sub_ids}` Berhasil dihapus dari daftar F-Subs.**",
                reply_markup=keyb,
            )


@HANDLER.CALLBACK_FSUB("^set_text")
async def cos_text(client, cq):
    user_id = cq.from_user.id
    owner = DB.get_var(client.me.id, "OWNER")
    DB.get_list_from_var(client.me.id, "ADMINS")
    costum_text = DB.get_var(client.me.id, "MSG_JOIN")
    keyb = ikb(
        [
            [("Set Costum Msg", "add_msg")],
            [("Back", "users_settings")],
            [("Close", "closed")],
        ]
    )
    if user_id == int(owner):
        msg = f"**Saat ini pesan start kamu:**\n\n{costum_text}"
        return await cq.edit_message_text(msg, reply_markup=keyb)


@HANDLER.CALLBACK_FSUB("^(add_msg)")
async def etc_msg(client, cq):
    user_id = cq.from_user.id
    message = cq.message
    owner = DB.get_var(client.me.id, "OWNER")
    adm = DB.get_list_from_var(client.me.id, "ADMINS")
    keyb = ikb(
        [
            [("Set Costum Msg", "add_msg")],
            [("Back", "users_settings")],
            [("Close", "closed")],
        ]
    )
    if user_id in adm and user_id == int(owner):
        await cq.answer()
        msg_text = await client.ask(
            user_id,
            "<blockquote><b>Silahkan kirim text untuk dijadikan pesan wajib join.</b></blockquote>",
            filters=filters.text,
        )
        if await cancel(message, msg_text.text):
            return
        DB.set_var(client.me.id, "MSG_JOIN", msg_text.text)
        return await message.reply(
            f"<blockquote><b>Pesan wajib join diatur ke:\n\n{msg_text.text}</blockquote></b>",
            reply_markup=keyb,
        )


@HANDLER.CALLBACK_FSUB("^start_back")
async def start_back(client, cq):
    message = cq.message
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
