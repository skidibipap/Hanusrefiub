import asyncio
import os
import zipfile
from datetime import datetime

from main.helper.keyboard import ikb
from pytz import timezone

from config import AKSES_DEPLOY, BOT_ID, LOG_GRUP
from main import bot, fsub

from ..database import DB, DB_PATH

waktu_jkt = timezone("Asia/Jakarta")


async def sending_user(user_id, msg):
    return await bot.send_message(LOG_GRUP, f"⛔ Laporan {user_id} {msg}")


async def CheckUsers():
    while True:
        await asyncio.sleep(15)
        total = DB.get_var(BOT_ID, "total_users")
        try:
            if len(fsub._bot) != total:
                now = datetime.now(waktu_jkt)
                timestamp = now.strftime("%Y-%m-%d_%H:%M")
                zip_filename = f"FSUB_{timestamp}.zip"
                with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(DB_PATH, os.path.basename(DB_PATH))
                caption = now.strftime("%d %B %Y %H:%M")
                await bot.send_document(LOG_GRUP, zip_filename, caption=caption)
                os.remove(zip_filename)
        except Exception as e:

            return await bot.send_message(LOG_GRUP, f"CheckUsers error: {str(e)}")


MSG_EXPIRED = """
<blockquote> <b>❏ Notifikasi</b>
<b>Bot :</b> <a href=tg://user?id={}>{} {}</a>
<b>ID:</b> <code>{}</code>
<b>Masa Aktif Telah Habis</b></blockquote>"""


"""
async def ExpiredBot():
    while True:
        await asyncio.sleep(10)
        for X in fsub._bot:
            try:
                wkt = datetime.now(timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M")
                exp = DB.get_expired_date(X.me.id)
                expir = exp.astimezone(waktu_jkt).strftime("%Y-%m-%d %H:%M")
                if expir == wkt:
                    owner = DB.get_var(X.me.id, "OWNER")
                    msg = MSG_EXPIRED.format(
                        X.me.id, X.me.first_name, X.me.last_name or "", X.me.id
                    )
                    keyb = ikb(
                        [
                            [
                                (
                                    "Perpanjang Klik Disini",
                                    f"https://t.me/{bot.me.username}",
                                    "url",
                                )
                            ]
                        ]
                    )
                    await bot.send_message(LOG_GRUP, msg, reply_markup=keyb)
                    await bot.send_message(owner, msg, reply_markup=keyb)
                    # DB.remove_ubot(X.me.id)
                    DB.rem_expired_date(X.me.id)
                    # DB.rm_all(X.me.id)
                    # fsub._bot.remove(X)
                    os.system(f"rm -rf {X.me.id}*")
            except Exception:
                pass
                #return await bot.send_message(LOG_GRUP, f"ExpiredBot error: {str(e)}")
"""


async def ExpiredBot():
    while True:
        await asyncio.sleep(10)
        min2h = DB.get_list_from_var(BOT_ID, "FSUB_EXPIRED_H")
        list_done = DB.get_list_from_var(BOT_ID, "FSUB_EXPIRED")
        for X in fsub._bot:
            try:
                now = datetime.now(timezone("Asia/Jakarta"))
                exp = DB.get_expired_date(X.me.id)
                expir = exp.astimezone(waktu_jkt)
                time_diff = expir - now
                if 47 <= time_diff.total_seconds() <= 49 * 3600:
                    owner = DB.get_var(X.me.id, "OWNER")
                    msg = f"""
<blockquote><b>⚠️ Peringatan: Masa aktif akan berakhir dalam 2 hari
Bot ID: `{X.me.id}`
Nama Bot: <u>{X.me.mention}</u>
Tanggal Expired: {expir.strftime('%Y-%m-%d %H:%M')}</blockquote></b>"""

                    keyb = ikb(
                        [
                            [
                                (
                                    "Perpanjang Klik Disini",
                                    f"https://t.me/{bot.me.username}",
                                    "url",
                                )
                            ]
                        ]
                    )
                    if X.me.id not in min2h:
                        DB.add_to_var(BOT_ID, "FSUB_EXPIRED_H", X.me.id)
                        await bot.send_message(LOG_GRUP, msg, reply_markup=keyb)
                        await X.send_message(owner, msg, reply_markup=keyb)
                    else:
                        pass
                elif expir.strftime("%Y-%m-%d %H:%M") == now.strftime("%Y-%m-%d %H:%M"):
                    owner = DB.get_var(X.me.id, "OWNER")
                    msg = MSG_EXPIRED.format(
                        X.me.id, X.me.first_name, X.me.last_name or "", X.me.id
                    )
                    keyb = ikb(
                        [
                            [
                                (
                                    "Perpanjang Klik Disini",
                                    f"https://t.me/{bot.me.username}",
                                    "url",
                                )
                            ]
                        ]
                    )
                    if X.me.id not in list_done:
                        DB.add_to_var(BOT_ID, "FSUB_EXPIRED", X.me.id)
                        await bot.send_message(LOG_GRUP, msg, reply_markup=keyb)
                        await X.send_message(owner, msg, reply_markup=keyb)
                        DB.rem_expired_date(X.me.id)
                        os.system(f"rm -rf {X.me.id}*")
                    else:
                        pass

            except Exception:
                # return await bot.send_message(LOG_GRUP, f"ExpiredBot error: {str(e)}")
                pass

        await asyncio.sleep(10)


async def Clean_Accses():
    while True:
        await asyncio.sleep(360)
        for org in AKSES_DEPLOY:
            try:
                seles = DB.get_list_from_var(BOT_ID, "seller")
                if org not in seles:
                    AKSES_DEPLOY.remove(org)
            except Exception as e:
                return await bot.send_message(LOG_GRUP, f"Clean_Accses error: {str(e)}")
