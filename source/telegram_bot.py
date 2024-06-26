import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from kleinanzeigenbot import KleinanzeigenBot, re

personal_chat_id = 0

registered_bots: list[KleinanzeigenBot] = []
filters = []
fetch_job_started = False

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    start the program

    :param update: [TODO:description]
    :param context: [TODO:description]
    """

    message = f"welcome. Available commands are:\n\n/start_bots  -- start fetch with registered bots\n/stop -- stop fetch job\n/add_bot <name> <link> -- add a bot\n/clear_bots -- stop and clear list of bots\n/status -- get status informations"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def start_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # startup Logic here
    if len(registered_bots) <= 0:
        await bot_message(update, context, "No registered Bots!")

    global fetch_job_started

    if not fetch_job_started:
        fetch_job_started = True
        context.job_queue.run_repeating(fetch_articles, interval=120, first=10)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Bot is now running!"
        )
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Bot is already running!"
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global fetch_job_started

    for job in context.job_queue.jobs():
        job.schedule_removal()

    fetch_job_started = False

    await bot_message(update, context, "Fetch job stopped")


async def bot_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
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
    # add a new bot to the registered bots
    args = context.args

    if args is None:
        return

    # sanitize input
    if len(args) != 2:
        await bot_message(
            update,
            context,
            "add_bot command requires two arguments. usage:\n/add_bot <name> <link>",
        )
        return

    bot = KleinanzeigenBot(args[1], args[0])

    if bot.invalid_link_flag:
        await bot_message(update, context, "something went wrong, link is not valid!")
        return

    global registered_bots
    registered_bots.append(bot)

    global fetch_job_started
    if not fetch_job_started:
        # first bot added
        fetch_job_started = True
        context.job_queue.run_repeating(fetch_articles, interval=120, first=10)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"added new bot: {bot.name}"
    )


async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    for filter in args:
        filters.append(filter)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"added new filter(s): {filter}"
    )


async def show_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(filters) <= 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"No active filters"
        )
        return
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"active filters: {filters}"
    )


async def clear_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Clear all current filters.

    :param update: the current update
    :param context: the current context
    """
    filters.clear()

    await bot_message(update, context, "cleared all filters")


async def clear_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Clears the list of Bots.

    :param update: the current update
    :param context: the current context
    """

    info = ""
    global fetch_job_started

    if fetch_job_started:
        fetch_job_started = False
        for job in context.job_queue.jobs():
            job.schedule_removal()

        info += "stopped fetch job\n"

    info += "cleared registered bots. removed bots:"

    for bot in registered_bots:
        info += f"\n\n{bot.name} -- {bot.url}"
    registered_bots.clear()

    await context.bot.send_message(chat_id=update.effective_chat.id, text=info)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = "status: " + (
        '<b style="color:#00FF00">running</b>'
        if fetch_job_started
        else '<b style="color:#FF0000">idle</b>'
    )
    info += "\nregistered bots:"
    for bot in registered_bots:
        info += f"\n{bot.name}: {bot.num_items()} items registered"
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=info, parse_mode="HTML"
    )


async def remove_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if args is None:
        return

    if len(args) != 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="wrong number of arguments. usage:\n/remove_bot <name>",
        )
        return

    global registered_bots
    before = len(registered_bots)
    if before <= 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="There are no registered bots"
        )
        return
    registered_bots = list(filter(lambda x: x.name != args[0], registered_bots))

    after = len(registered_bots)
    if after < before:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"removed bot {args[0]}"
        )
    if after <= 0:
        await stop(update, context)


async def fetch_articles(context: ContextTypes.DEFAULT_TYPE):
    for bot in registered_bots:
        articles = bot.get_new_articles()

        if len(articles) <= 0:
            return

        # await context.bot.send_message(chat_id=personal_chat_id, text=f"I found some new articles for your search {bot.name}!")

        for a in articles:
            if not a.check_filters(filters):
                continue
            message = f"<b>{a.title}</b>\n{a.price} -- <i>{a.location}</i>\nhttps://www.kleinanzeigen.de{a.url}\n<i>search: {bot.name}</i>"
            await context.bot.send_message(
                chat_id=personal_chat_id, text=message, parse_mode="HTML"
            )


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
