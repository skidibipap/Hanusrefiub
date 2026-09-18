import uvloop

uvloop.install()

import asyncio
import importlib
import logging
import os
import re
import shlex
import subprocess
import sys
import traceback
from datetime import datetime

from pyrogram import Client, enums
from pyrogram.errors import *
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram.types import BotCommand
from kurimod import listen
from pytz import timezone

from config import (ADMIN_IDS, AKSES_DEPLOY, API_HASH, API_ID, BOT_ID,
                    BOT_TOKEN, DB_NAME, LOG_GRUP)
from main.database import DB
from main.plugins import BOT_PLUGINS


class JakartaFormatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)
        jakarta_tz = timezone("Asia/Jakarta")
        return dt.astimezone(jakarta_tz)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


class ConnectionHandler(logging.Handler):
    def emit(self, record):
        if any(
            error_type in record.getMessage()
            for error_type in ["TimeoutError", "OSError"]
        ):
            os.execl(sys.executable, sys.executable, "-m", "main")


logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("pyrogram.client").setLevel(logging.WARNING)
logging.getLogger("pyrogram.session.auth").setLevel(logging.CRITICAL)
logging.getLogger("pyrogram.session.session").setLevel(logging.CRITICAL)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = JakartaFormatter(
    "[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M"
)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
connection_handler = ConnectionHandler()
logger.addHandler(connection_handler)
logger.addHandler(stream_handler)

list_error = []


class BaseBot(Client):
    _bot = []
    _bot_id = []
    _seles_ids = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_mention(self, me, logs=False, no_tag=False):
        name = f"{me.first_name} {me.last_name}" if me.last_name else me.first_name
        link = f"tg://user?id={me.id}"
        return (
            f"{me.id}|{name}"
            if logs
            else name if no_tag else f"<a href={link}>{name}</a>"
        )

    async def bash(self, cmd):
        try:
            process = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            err = stderr.decode().strip()
            out = stdout.decode().strip()
            return out, err
        except NotImplementedError:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            stdout, stderr = process.communicate()
            err = stderr.decode().strip()
            out = stdout.decode().strip()
            return out, err

    async def run_cmd(self, cmd):
        args = shlex.split(cmd)
        try:
            process = await asyncio.create_subprocess_exec(
                *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return (
                stdout.decode("utf-8", "replace").strip(),
                stderr.decode("utf-8", "replace").strip(),
                process.returncode,
                process.pid,
            )
        except NotImplementedError:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            stdout, stderr = process.communicate()
            return (
                stdout.decode("utf-8", "replace").strip(),
                stderr.decode("utf-8", "replace").strip(),
                process.returncode,
                process.pid,
            )

    async def aexec(self, code, c, m):
        exec(
            "async def __aexec(c, m): "
            + "\n chat = m.chat"
            + "\n r = m.reply_to_message"
            + "\n c = c"
            + "\n m = m"
            + "\n p = print"
            + "".join(f"\n {l_}" for l_ in code.split("\n"))
        )
        return await locals()["__aexec"](c, m)

    async def shell_exec(self, code, treat=True):
        process = await asyncio.create_subprocess_shell(
            code, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )

        stdout = (await process.communicate())[0]
        if treat:
            stdout = stdout.decode().strip()
        return stdout, process

    async def extract_userid(self, m, t):
        def is_int(t):
            try:
                int(t)
            except ValueError:
                return False
            return True

        text = t.strip()

        if is_int(text):
            return int(text)

        entities = m.entities
        entity = entities[1 if m.text.startswith("/") else 0]
        if entity.type == enums.MessageEntityType.MENTION:
            return (await self.get_users(text)).id
        if entity.type == enums.MessageEntityType.TEXT_MENTION:
            return entity.user.id
        return None

    async def extract_user_and_reason(self, m, s=False):
        args = m.text.strip().split()
        text = m.text
        rg = None
        reason = None
        if m.reply_to_message:
            reply = m.reply_to_message
            if not reply.from_user:
                if reply.sender_chat and reply.sender_chat != m.chat.id and s:
                    id_ = reply.sender_chat.id
                else:
                    return None, None
            else:
                id_ = reply.from_user.id

            if len(args) < 2:
                reason = None
            else:
                reason = text.split(None, 1)[1]
            return id_, reason

        if len(args) == 2:
            rg = text.split(None, 1)[1]
            return await self.extract_userid(m, rg), None

        if len(args) > 2:
            rg, reason = text.split(None, 2)[1:]
            return await self.extract_userid(m, rg), reason

        return rg, reason

    async def extract_user(self, m):
        return (await self.extract_user_and_reason(m))[0]

    async def set_cmds_fsub(self, client):
        try:
            return await client.set_bot_commands(
                [
                    BotCommand("start", "Mulai bot."),
                    BotCommand("help", "Melihat menu bantuan bot."),
                    BotCommand("addpic", "Mengatur foto untuk auto post konten bot."),
                    BotCommand("users", "Mengecek pengguna Bot."),
                    BotCommand("broadcast", "Kirim pesan siaran ke pengguna bot."),
                    BotCommand("addadmin", "Menambahkan admin."),
                    BotCommand("deladmin", "Menghapus admin."),
                    BotCommand("getadmin", "Melihat admin."),
                    BotCommand("info", "Cek status bot fsub."),
                    BotCommand("ping", "Cek ping bot."),
                    BotCommand("uptime", "Cek waktu bot."),
                    BotCommand("addbutton", "Tambah button bot."),
                    BotCommand("delbutton", "Hapus button bot."),
                    BotCommand("getbutton", "Cek button bot."),
                    BotCommand("addkonten", "Tambah Channel konten."),
                    BotCommand("delkonten", "Hapus Channel konten."),
                    BotCommand("getkonten", "Cek Channel konten."),
                    BotCommand("limitbutton", "Cek limit button."),
                    BotCommand("limitkonten", "Cek limit konten."),
                    BotCommand("protect", "Batasi konten dibot."),
                    BotCommand("setdb", "Atur database bot."),
                    BotCommand("getdb", "Cek database bot."),
                    BotCommand("setmsg", "Atur pesan wajib join."),
                    BotCommand("batch", "Untuk membuat link lebih dari satu file."),
                    BotCommand("genlink", "Buat tautan untuk satu posting."),
                ]
            )
        except Exception as er:
            logger.error(str(er))

    async def set_cmds_bot(self, client):
        try:
            return await client.set_bot_commands(
                [
                    BotCommand("start", "Mulai bot."),
                    BotCommand("help", "Melihat menu bantuan bot."),
                    BotCommand("restore", "Restore database."),
                    BotCommand("buser", "Mengecek pengguna Bot."),
                    BotCommand("broadcast", "Kirim pesan siaran ke pengguna bot"),
                    BotCommand("addexpired", "Menambahkan masa aktif bot"),
                    BotCommand("addseller", "Menambahkan seller"),
                    BotCommand("delseller", "Menghapus seller"),
                    BotCommand("getseller", "Melihat seller"),
                    BotCommand("gban", "Blokir pengguna "),
                    BotCommand("ungban", "Buka blokir pengguna"),
                    BotCommand("gbanlist", "List pengguna diblokir"),
                    BotCommand("trash", "Dump"),
                    BotCommand("reboot", "Restart Bot"),
                    BotCommand("update", "Update bot"),
                    BotCommand("eval", "Execute kode"),
                    BotCommand("sh", "Jalankan perintah shell"),
                    BotCommand("info", "Cek status bot fsub"),
                    BotCommand("ping", "Cek ping bot"),
                    BotCommand("uptime", "Cek waktu bot"),
                    BotCommand("limitbutton", "Atur batas button bot"),
                    BotCommand("limitkonten", "Atur batas Channel Konten bot"),
                ]
            )
        except Exception as er:
            logger.error(str(er))


class FsubBot(BaseBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_message(self, filters=None, group=-1):
        def decorator(func):
            for ub in self._bot:
                ub.add_handler(MessageHandler(func, filters), group)
            return func

        return decorator

    def on_callback_query(self, filters=None, group=-1):
        def decorator(func):
            for ub in self._bot:
                ub.add_handler(CallbackQueryHandler(func, filters), group)
            return func

        return decorator

    async def start(self):
        await super().start()
        full = f"<a href=tg://user?id={self.me.id}>{self.me.first_name} {self.me.last_name or ''}</a>"
        DB.add_userdata(
            self.me.id,
            self.me.first_name,
            self.me.last_name,
            self.me.username,
            self.me.mention,
            full,
            self.me.id,
        )
        self._bot_id.append(self.me.id)
        self._bot.append(self)
        logger.info(
            f"🔥 {self.me.username} Starting Bot {self.me.id}|{self.me.first_name}"
        )


class Bot(BaseBot):
    def __init__(self, **kwargs):
        super().__init__(
            name="bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            in_memory=True,
            **kwargs,
        )

    def on_message(self, filters=None, group=-1):
        def decorator(func):
            self.add_handler(MessageHandler(func, filters), group)
            return func

        return decorator

    def on_callback_query(self, filters=None, group=-1):
        def decorator(func):
            self.add_handler(CallbackQueryHandler(func, filters), group)
            return func

        return decorator

    async def load_seles(self):
        seles = DB.get_list_from_var(self.me.id, "seller")
        for p in ADMIN_IDS:
            if p not in seles:
                DB.add_to_var(self.me.id, "seller", p)
            if p not in AKSES_DEPLOY:
                AKSES_DEPLOY.append(p)

    async def start(self):
        await super().start()
        await self.set_cmds_bot(self)

        logger.info("✅ Successed Setup")
        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention
        user_bots = DB.get_userbots()
        total_bots = len(user_bots)
        message = "🔥**Fsub berhasil diaktifkan**🔥\n" f"✅ **Total Bot: {total_bots}**"
        DB.set_var(BOT_ID, "total_users", total_bots)
        await self.send_message(LOG_GRUP, f"<blockquote>{message}</blockquote>")
        logger.info(f"🔥 {self.username} Bot Started 🔥")


bot = Bot()
fsub = FsubBot(name="Fsub", plugins=dict(root="main/plugins"))
