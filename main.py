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

    @bot.slash_command()
    @discord.option("search", input_type=str)
    async def music(ctx: discord.ApplicationContext, search: str):
        await ctx.respond(f"Pong! Latency is {bot.latency} and search term is {search}")


    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    main()