import dotenv
import os
import logging
import discord
import requests
import json
import isodate

def setup_logging():
    logging.basicConfig(level=logging.INFO)

def strip_yt_api_key_from_dict(d: dict):
    return {k:v for k, v in d.items() if k != "key"}

def youtube_api_search_with(base: str = "https://www.googleapis.com/youtube/v3/search", **search_args):
    logging.info("Sending GET request to Youtube API /search endpoint with: %s", strip_yt_api_key_from_dict(search_args))
    search_args["key"] = os.getenv("YT_API_KEY")
    result = requests.get(base, params=search_args)
    return result

def youtube_api_get_videos(ids: list[str], base: str = "https://www.googleapis.com/youtube/v3/videos", **search_args):
    search_args["id"] = ','.join(ids)
    logging.info("Sending GET request to Youtube API /videos endpoint with: %s", strip_yt_api_key_from_dict(search_args))
    search_args["key"] = os.getenv("YT_API_KEY")
    result = requests.get(base, params=search_args).json()
    return result

def build_embed(video_ids: list[str]):
    video_info_list = youtube_api_get_videos(video_ids, part="snippet,contentDetails", regionCode="SE")
    embed = discord.Embed(title="Choose song", color=discord.Color.blue())
    for i, video_info in enumerate(video_info_list["items"]):
        duration = isodate.parse_duration(video_info["contentDetails"]["duration"])
        title = video_info["snippet"]["title"]
        artist = video_info["snippet"]["channelTitle"]
        embed_field = discord.EmbedField(
            name=f"{i+1}. {title} ({duration.seconds//60:02d}:{duration.seconds%60:02d})",
            value=f"Uploaded by {artist}",
            inline=False
        )
        embed.append_field(embed_field)
    return embed

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
        # await ctx.respond(f"Pong! Latency is {bot.latency} and search term is {search}")
        response = youtube_api_search_with(part="snippet", maxResults=5, regionCode="SE", safeSearch="none", type="video", q=search)
        videos = response.json().get("items")
        video_ids = [video["id"]["videoId"] for video in videos]
        embed = build_embed(video_ids)
        await ctx.send(embed=embed)

    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    main()