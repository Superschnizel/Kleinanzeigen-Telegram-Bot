from typing import List

from telegram.ext import ContextTypes, Job
from source.kleinanzeigenbot import KleinanzeigenBot, KleinanzeigenItem


class ChatClient:
    def __init__(self, chat_id: int) -> None:
        self.registered_bots: List[KleinanzeigenBot] = []
        self.id: int = chat_id
        self.fetch_job: Job | None = None
        self.filters: List[str] = []

    def fetch_job_running(self) -> bool:
        return self.fetch_job != None

    async def start_fetch_job(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Start the fetch job for this ChatClient

        :param context: the current context.
        """

        # check if there are any bots to start
        if len(self.registered_bots) <= 0:
            await context.bot.send_message(
                chat_id=self.id,
                text=f"There are not bots to sart yet. Try adding some with /add_bot",
            )
            return

        if context.job_queue is None:
            await context.bot.send_message(
                chat_id=self.id,
                text=f"Could not start due to internal error 501",
            )
            print("context has no job_queue")
            return

        if self.fetch_job_running():
            await context.bot.send_message(
                chat_id=self.id,
                text=f"Fetch job is already running.",
            )
            return

        # Create and schedule the job
        self.fetch_job = context.job_queue.run_repeating(self.fetch_articles, interval=120, first=10)
        await context.bot.send_message(
            chat_id=self.id,
            text=f"Fetch job for {len(self.registered_bots)} bots is now running!",
        )

    def stop_fetch_job(self) -> None:
        if self.fetch_job is None:
            print("tried to remove none running job")
            return

        self.fetch_job.schedule_removal()
        self.fetch_job = None

    async def fetch_articles(self, context: ContextTypes.DEFAULT_TYPE):
        for bot in self.registered_bots:
            articles = bot.get_new_articles()

            if len(articles) <= 0:
                return

            for a in articles:
                if not a.check_filters(self.filters):
                    continue
                message = (
                    f"<b>{a.title}</b>\n{a.price} -- <i>{a.location}</i>\nhttps://www.kleinanzeigen.de{a.url}\n<i>search: {bot.name}</i>"
                )
                await context.bot.send_message(chat_id=self.id, text=message, parse_mode="HTML")

    def add_bot(self, bot: KleinanzeigenBot):
        self.registered_bots.append(bot)

    def remove_bot(self, link: str) -> bool:
        before = len(self.registered_bots)

        self.registered_bots = list(filter(lambda x: x.name != link, self.registered_bots))

        after = len(self.registered_bots)

        return after < before

    def add_filter(self, filter: str):
        self.filters.append(filter)
