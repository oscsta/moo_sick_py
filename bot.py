import discord
import logging
import dotenv

class MooSick(discord.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        logging.info("Logged in as: %s (ID: %d)", self.user.name, self.user.id)
        logging.info("------")