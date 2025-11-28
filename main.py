import dotenv
import os
import logging
import discord
import requests
import json

def setup_logging():
    logging.basicConfig(level=logging.INFO)

def query_yt_search_api_with(**search_args):
    base = "https://www.googleapis.com/youtube/v3/search"
    result = requests.get(base, params=search_args)
    return result

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
        response = query_yt_search_api_with(part="snippet", maxResults=5, regionCode="SE", safeSearch="none", type="video", q=search, key=os.getenv("YT_API_KEY"))
        print(json.dumps(response.json(), indent=2))


    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    main()