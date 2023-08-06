import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from kleinanzeigenbot import KleinanzeigenBot

API_TOKEN = '6509130308:AAHdEMCtiYulOgAf7EFDFFHc3QwaED1loPI'
CHAT_ID = 589158099
TEST_URL = 'https://www.kleinanzeigen.de/s-wohnung-mieten/berlin/preis::1000/c203l3331+wohnung_mieten.verfuegbarm_i:10%2C+wohnung_mieten.verfuegbary_i:2023%2C'

registered_bots = []
fetch_job_started = False

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = f"welcome. Available commands are:\n\n/start_bots  -- start fetch with registered bots\n/stop -- stop fetch job\n/add_bot <name> <link> -- add a bot\n/clear_bots -- stop and clear list of bots\n/status -- get status informations"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

async def start_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # startup Logic here
    if len(registered_bots) <= 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No registered Bots!")

    global fetch_job_started
    if not fetch_job_started:
        fetch_job_started = True
        context.job_queue.run_repeating(fetch_articles, interval=120, first=10)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Bot is now running!")
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Bot is already running!")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global fetch_job_started
    for job in context.job_queue.jobs():
        job.schedule_removal()
    fetch_job_started = False
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Fetch job stopped.")

async def add_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #add a new bot to the registered bots
    args = context.args
    # sanitize input
    if len(args) != 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="add_bot command requires two arguments. usage:\n/add_bot <name> <link>")
        return

    bot = KleinanzeigenBot(args[1], args[0])

    if bot.invalid_link_flag:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="something went wrong, link is not valid!")
        return

    global registered_bots
    registered_bots.append(bot)

    global fetch_job_started
    if not fetch_job_started:
        # first bot added
        fetch_job_started = True
        context.job_queue.run_repeating(fetch_articles, interval=120, first=10)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"added new bot: {bot.name}")

async def clear_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):

    info = ""
    global fetch_job_started
    if fetch_job_started:
        fetch_job_started = False
        for job in context.job_queue.jobs():
            job.schedule_removal()
        info += "stopped fetch job\n"

    info += 'cleared registered bots. removed bots:'
    for bot in registered_bots:
        info += f"\n\n{bot.name} -- {bot.url}"
    registered_bots.clear()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=info)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = "status: " + ("running" if fetch_job_started else "idle")
    info += "\nregistered bots:"
    for bot in registered_bots:
        info += f"\n{bot.name}"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=info)

async def remove_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="wrong number of arguments. usage:\n/remove_bot <name>")
        return
    
    global registered_bots
    before = len(registered_bots)
    if before <= 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="There are no registered bots")
        return
    registered_bots = list(filter(lambda x: x.name != args[0], registered_bots))

    after = len(registered_bots)
    if after < before:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"removed bot {args[0]}")
    if after <= 0:
        await stop(update, context)



async def fetch_articles(context: ContextTypes.DEFAULT_TYPE):
    for bot in registered_bots:
        articles = bot.get_new_articles()

        if len(articles) <= 0:
            return

        await context.bot.send_message(chat_id=CHAT_ID, text=f"I found some new articles for your search {bot.name}!")

        for a in articles:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"https://www.kleinanzeigen.de{a}")



if __name__ == '__main__':
    application = ApplicationBuilder().token(API_TOKEN).build()
    job_queue = application.job_queue

    start_handler = CommandHandler('start', start)
    start_bots_handler = CommandHandler('start_bots', start_bots)
    stop_handler = CommandHandler('stop', stop)
    add_bot_handler = CommandHandler('add_bot', add_bot)
    clear_bots_handler = CommandHandler('clear_bots', clear_bots)
    status_handler = CommandHandler('status', status)
    remove_bot_handler = CommandHandler('remove_bot', remove_bot)
    application.add_handler(start_handler)
    application.add_handler(start_bots_handler)
    application.add_handler(stop_handler)
    application.add_handler(add_bot_handler)
    application.add_handler(clear_bots_handler)
    application.add_handler(status_handler)
    application.add_handler(remove_bot_handler)
    
    # drop_pending_updates discards all updates before startup
    application.run_polling(drop_pending_updates=True)