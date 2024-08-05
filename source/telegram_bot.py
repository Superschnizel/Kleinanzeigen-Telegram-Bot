import logging
import os
from functools import reduce
from typing import Dict, List
from requests.exceptions import RetryError
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from kleinanzeigenbot import KleinanzeigenBot, re
from chat_client import ChatClient

personal_chat_id = 0

registered_bots_dict: Dict[int, ChatClient] = {}
# filters = []
# fetch_job_started = False

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Register the current chat with the bot.

    :param update: the current update
    :param context: the current context
    """

    chat = update.effective_chat

    if chat is None:
        print("could not get id for effective_chat!")
        return

    chat_id = chat.id

    if chat_id in registered_bots_dict.keys():
        await bot_respond(update, context, "This chat is already registered.")
        return

    # add the chat id to the registered ids.
    registered_bots_dict[chat_id] = ChatClient(chat_id)
    await bot_respond(update, context, "successfully registered this chat")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    start the program

    :param update: [TODO:description]
    :param context: [TODO:description]
    """

    message = f"welcome. Available commands are:\n\n/start_bots  -- start fetch with registered bots\n/stop -- stop fetch job\n/add_bot <name> <link> -- add a bot\n/clear_bots -- stop and clear list of bots\n/status -- get status informations"
    await bot_respond(update, context, message)


async def get_chat_client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ChatClient | None:
    """
    Check if the current chat id already has a registered chatClient.

    :param update: the current update
    :param context: the current context
    :return: the current chat_id or -1
    """
    if update.effective_chat is None:
        print("could not get id for effective_chat!")
        return None
    chat_id = update.effective_chat.id

    if not (chat_id in registered_bots_dict.keys()):
        await register(update, context)

    return registered_bots_dict[chat_id]


async def start_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start the Fetch job for the current chat id.

    :param update: the current update.
    :param context: the current context.
    """
    chatClient = await get_chat_client(update, context)
    if chatClient == None:
        return

    await chatClient.start_fetch_job(context)

    await bot_respond(update, context, "Fetch job started")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Stop the Fetch job for the current chat id, if it is running.

    :param update: the current update.
    :param context: the current context
    """
    chatClient = await get_chat_client(update, context)
    if chatClient == None:
        return

    if not chatClient.fetch_job_running():
        await bot_respond(
            update,
            context,
            "Fetch job is not running yet. Start Fetch job with /start_bots",
        )

    chatClient.stop_fetch_job()

    await bot_respond(update, context, "Fetch job stopped")


async def bot_respond(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    Send a message based on the current context to the sender given in Update.

    :param update: the current update
    :param context: the current context
    :param text: the message to be sent
    """
    chat = update.effective_chat

    if chat is None:
        print("could not get id for effective_chat!")
        return

    await context.bot.send_message(
        chat_id=chat.id,
        text=text,
    )


async def add_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add a link to be checked for new items

    :param update: the current update
    :param context: the current context
    """
    chatClient = await get_chat_client(update, context)
    if chatClient == None:
        return

    # add a new bot to the registered bots
    args = context.args

    if args is None:
        return

    # sanitize input
    if len(args) != 2:
        await bot_respond(
            update,
            context,
            "add_bot command requires two arguments. usage:\n/add_bot <name> <link>",
        )
        return

    bot = KleinanzeigenBot(args[1], args[0])

    if bot.invalid_link_flag:
        await bot_respond(update, context, "something went wrong, link is not valid!")
        return

    chatClient.add_bot(bot)

    await bot_respond(update, context, f"added new bot: {bot.name}")


async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatClient = await get_chat_client(update, context)
    if chatClient == None:
        return

    args = context.args

    if args == None:
        return

    for filter in args:
        chatClient.add_filter(filter)

    filterList = reduce(lambda a, b: a + "\n- " + b, chatClient.filters, "\n- ")
    await bot_respond(update, context, f"added new filter(s): {filterList}")


async def show_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatClient = await get_chat_client(update, context)
    if chatClient == None:
        return

    if len(chatClient.filters) <= 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"No active filters")
        return

    filterList = reduce(lambda a, b: a + "\n- " + b, chatClient.filters, "\n- ")
    await bot_respond(update, context, f"current filter(s): {filterList}")


async def clear_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Clear all current filters.

    :param update: the current update
    :param context: the current context
    """
    chatClient = await get_chat_client(update, context)
    if chatClient == None:
        return

    chatClient.filters.clear()

    await bot_respond(update, context, "cleared all filters")


async def clear_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Clears the list of Bots.

    :param update: the current update
    :param context: the current context
    """
    chatClient = await get_chat_client(update, context)
    if chatClient == None:
        return

    # stop running fetch jobs.
    chatClient.stop_fetch_job()

    info = "Cleared registered bots. removed bots:"

    for bot in chatClient.registered_bots:
        info += f"\n- {bot.name} -- {bot.url}"
    chatClient.registered_bots.clear()

    await bot_respond(update, context, info)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatClient = await get_chat_client(update, context)
    if chatClient == None:
        return

    info = "status: " + ('<b style="color:#00FF00">running</b>' if chatClient.fetch_job_running() else '<b style="color:#FF0000">idle</b>')
    info += "\nregistered links:"
    for bot in chatClient.registered_bots:
        info += f"\n{bot.name}: {bot.num_items()} items registered"

    await context.bot.send_message(chat_id=chatClient.id, text=info, parse_mode="HTML")


async def remove_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if args is None:
        return

    if len(args) != 1:
        await bot_respond(
            update,
            context,
            text="wrong number of arguments. usage:\n/remove_bot <name>",
        )
        return

    chatClient = await get_chat_client(update, context)
    if chatClient == None:
        return

    if not chatClient.remove_bot(args[0]):
        await bot_respond(update, context, "could not remove bot from active list. are you sure it exists?")
        return

    message = f"successfully removed {args[0]}."

    if len(chatClient.registered_bots) <= 0:
        message += "\nStopping fetch job, because there are no more active bots."
        chatClient.stop_fetch_job()


# async def fetch_articles(context: ContextTypes.DEFAULT_TYPE):
#     for bot in registered_bots:
#         articles = bot.get_new_articles()
#
#         if len(articles) <= 0:
#             return
#
#         # await context.bot.send_message(chat_id=personal_chat_id, text=f"I found some new articles for your search {bot.name}!")
#
#         for a in articles:
#             if not a.check_filters(filters):
#                 continue
#             message = f"<b>{a.title}</b>\n{a.price} -- <i>{a.location}</i>\nhttps://www.kleinanzeigen.de{a.url}\n<i>search: {bot.name}</i>"
#             await context.bot.send_message(chat_id=personal_chat_id, text=message, parse_mode="HTML")


if __name__ == "__main__":

    print(os.getcwd())

    try:
        with open("token.txt") as f:
            lines = f.readlines()
            token = lines[0].replace("\n", "")
            personal_chat_id = int(lines[1])
    except Exception as e:
        print(
            f"something went wrong while trying to read 'token.txt', please make sure that the file is in located in the working directory: {os.getcwd()}\n {e}"
        )
        raise SystemExit

    print(token)
    print(personal_chat_id)

    application = ApplicationBuilder().token(token).build()
    job_queue = application.job_queue

    start_handler = CommandHandler("start", start)
    start_bots_handler = CommandHandler("start_bots", start_bots)
    stop_handler = CommandHandler("stop", stop)
    add_bot_handler = CommandHandler("add_bot", add_bot)
    clear_bots_handler = CommandHandler("clear_bots", clear_bots)
    status_handler = CommandHandler("status", status)
    remove_bot_handler = CommandHandler("remove_bot", remove_bot)
    add_filter_handler = CommandHandler("add_filter", add_filter)
    show_filters_handler = CommandHandler("show_filters", show_filters)
    clear_filter_handler = CommandHandler("clear_filters", clear_filters)

    application.add_handler(start_handler)
    application.add_handler(start_bots_handler)
    application.add_handler(stop_handler)
    application.add_handler(add_bot_handler)
    application.add_handler(clear_bots_handler)
    application.add_handler(status_handler)
    application.add_handler(remove_bot_handler)
    application.add_handler(add_filter_handler)
    application.add_handler(show_filters_handler)
    application.add_handler(clear_filter_handler)

    # drop_pending_updates discards all updates before startup
    application.run_polling(drop_pending_updates=True)
