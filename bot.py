import logging
import os
from datetime import datetime, timedelta
from typing import List
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PicklePersistence,
    TypeHandler,
    ApplicationHandlerStop,
)
from telegram.constants import ParseMode

from sgprapp.model import ApplicationRecord, ApplicationType
from sgprapp.datasource import crawl


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Set these env properly!
TOKEN = os.getenv("TOKEN", "")
ADMINS = set(map(int, os.getenv("ADMINS", "").split(",")))
PERSISTENT_DIR = os.getenv("PERSISTENT_DIR", "./")
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", 3600))


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        raise ApplicationHandlerStop  # stop other handlers
    if "chats" not in context.bot_data.keys():
        context.bot_data["chats"] = dict()


async def publish_to_all(context: ContextTypes.DEFAULT_TYPE):
    chats = context.bot_data["chats"]
    if len(chats) == 0:
        logger.info("Empty chats list, skip this publishing")
        return
    latest_sgprapp_records = crawl(
        urls={
            ApplicationType.PR: "http://sgprapp.com/listPage",
            ApplicationType.Citizen: "http://sgprapp.com/citizen",
        }
    )
    max_history = datetime.now() - timedelta(days=1)
    for chat_id, last_publish in chats.items():
        for type, entries in latest_sgprapp_records.items():
            if len(entries) == 0:
                continue
            last_update = last_publish.get(type, max_history)
            # This is for backward compatibility: previously we store the last item ID instead of last update time
            if not isinstance(last_update, datetime):
                last_update = max_history
            to_send: List[ApplicationRecord] = list()
            for entry in entries:
                if entry.last_update <= last_update:
                    break
                to_send.append(entry)
            to_send.reverse()  # reverse it to make sure older entries are sent out first
            for entry in to_send:
                logger.info(f"Sending {entry.id} to {chat_id}")
                await context.bot.send_message(
                    chat_id=chat_id, text=entry.formatted(), parse_mode=ParseMode.HTML
                )
                context.bot_data["chats"][chat_id][type] = entry.last_update


async def add_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        # try to add this chat
        this_chat_id = update.effective_chat.id
        context.args.append(this_chat_id)
    for chat_to_add in context.args:
        if chat_to_add in context.bot_data["chats"].keys():
            continue
        # an empty dict as this chat has no previous records
        context.bot_data["chats"][chat_to_add] = dict()
    await list_chat(update, context)


async def del_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        # try to add this chat
        this_chat_id = update.effective_chat.id
        context.args.append(this_chat_id)
    for chat_to_del in context.args:
        context.bot_data["chats"].pop(chat_to_del, None)
    await list_chat(update, context)


async def list_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "List of chats:\n"
    for chat_id, last_publish in context.bot_data["chats"].items():
        message += f"\n<code>{chat_id}</code>\n"
        for type, entry_id in last_publish.items():
            message += f"  {type.name}: <code>{entry_id}</code>\n"
    await update.effective_message.reply_html(message)


if __name__ == "__main__":

    persistence = PicklePersistence(
        filepath=os.path.join(PERSISTENT_DIR, "sgprapp_bot_data")
    )

    app = Application.builder().token(TOKEN).persistence(persistence).build()
    app.job_queue.run_repeating(
        publish_to_all, INTERVAL_SECONDS, 60
    )  # delay 60 seconds

    check_admin_handler = TypeHandler(Update, check_admin)
    app.add_handler(check_admin_handler, -1)

    add_chat_handler = CommandHandler("add_chat", add_chat)
    app.add_handler(add_chat_handler, 0)
    del_chat_handler = CommandHandler("del_chat", del_chat)
    app.add_handler(del_chat_handler, 0)
    list_chat_handler = CommandHandler("list_chat", list_chat)
    app.add_handler(list_chat_handler, 0)

    app.run_polling()
