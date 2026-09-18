import asyncio
import importlib
import os
import sys
from datetime import datetime

import croniter
from aiorun import run
from pyrogram.errors import (AccessTokenExpired, SessionRevoked,
                             UserDeactivated, UserDeactivatedBan)
from pytz import timezone

from main import LOG_GRUP, FsubBot, bot, list_error, logger
from main.database import DB
from main.helper.task import CheckUsers, Clean_Accses, ExpiredBot, sending_user
from main.plugins import BOT_PLUGINS

waktu_jkt = timezone("Asia/Jakarta")


def handle_remove_err(_ubot, message):
    DB.remove_ubot(int(_ubot["name"]))
    DB.rm_all(int(_ubot["name"]))
    DB.rem_expired_date(int(_ubot["name"]))
    logger.error(f"✅ {int(_ubot['name'])} {message}")
    data = {"user": int(_ubot["name"]), "error_msg": message}
    list_error.append(data)


async def start_ubot(_ubot):
    ubot_ = FsubBot(**_ubot)
    try:
        await ubot_.start()
        await ubot_.set_cmds_fsub(ubot_)
    except (SessionRevoked, AccessTokenExpired):
        handle_remove_err(_ubot, "Telah dihapus karna session revoked")
        logger.error(f"✅ {int(_ubot['name'])} Telah dihapus karna session revoked")
    except (UserDeactivatedBan, UserDeactivated):
        handle_remove_err(_ubot, "Telah dihapus karna deak")
        logger.error(f"✅ {int(_ubot['name'])} Telah dihapus karna deak")


async def send_error_messages():
    """Send error messages to users if any exist."""
    if list_error:
        await asyncio.gather(
            *(sending_user(error["user"], error["error_msg"]) for error in list_error)
        )


async def schedule_backup_and_restart():
    """Schedule daily backup at 23:00 and restart at 00:00."""
    cron = croniter.croniter("00 00 * * *", datetime.now(waktu_jkt))

    while True:
        try:
            next_run = cron.get_next(datetime)
            wait_time = (next_run - datetime.now(waktu_jkt)).total_seconds()
            logger.info(f"Scheduled restart in {wait_time} seconds.")
            await asyncio.sleep(wait_time)
            await bot.send_message(
                LOG_GRUP,
                "<blockquote><b>Restart Daily..\n\nTunggu beberapa menit bot sedang di Restart!!</b></blockquote>",
            )
            os.execl(sys.executable, sys.executable, "-m", "main")
        except Exception as e:
            logger.error(f"Schedule error: {str(e)}")


async def start_main_bot():
    """Start the main bot after userbots."""
    logger.info("🤖 Starting main bot...")
    await bot.start()
    await bot.load_seles()
    logger.info("✅ Main bot started successfully.")


async def start_userbots():
    """Start all userbots first."""
    logger.info("🔄 Starting userbots...")
    userbots = DB.get_userbots()
    tasks = [asyncio.create_task(start_ubot(ubot)) for ubot in userbots]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"❌ Error starting userbot {userbots[idx]['name']}: {result}")
            raise Exception(f"Userbot {userbots[idx]['name']} failed to start.")

    logger.info("✅ All userbots started successfully.")


async def start_task():
    task = [
        CheckUsers(),
        ExpiredBot(),
        Clean_Accses(),
        schedule_backup_and_restart(),
    ]
    for tsk in task:
        asyncio.create_task(tsk)


async def ImportPlugins():
    for mod in BOT_PLUGINS:
        importlib.reload(importlib.import_module(f"main.plugins.{mod}"))


async def start_main():
    await start_userbots()
    await start_main_bot()
    await ImportPlugins()
    await start_task()
    await send_error_messages()


async def stop_main():
    logger.info("Stopping task and bot")
    await bot.stop()
    DB.close()


if __name__ == "__main__":
    run(
        start_main(),
        shutdown_callback=stop_main,
    )
