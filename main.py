import dotenv
import os
import logging
import discord

def setup_logging():
    logging.basicConfig(level=logging.INFO)

def main():
    dotenv.load_dotenv()
    setup_logging()

    bot = discord.Bot()

    @bot.event
    async def on_ready():
        assert bot.user is not None, "bot.user was None"

        logging.info("Logged in as: %s (ID: %d)", bot.user.name, bot.user.id)
        logging.info("------")

    @bot.command()
    async def play(ctx: discord.ApplicationContext):
        await ctx.respond(f"Pong! Latency is {bot.latency}")


    bot.run(os.getenv("DISCORD_API_KEY"))

if __name__ == "__main__":
    main()