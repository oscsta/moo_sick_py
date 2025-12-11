import asyncio
from typing import Self
import dotenv
import os
import logging
import discord
import requests
import json
import isodate
import yt_dlp



def setup_logger():
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    return logger

logger = setup_logger()


def strip_yt_api_key_from_dict(d: dict):
    return {k:v for k, v in d.items() if k != "key"}

def youtube_api_search_with(base: str = "https://www.googleapis.com/youtube/v3/search", **search_args):
    logger.info("Sending GET request to Youtube API /search endpoint with: %s", strip_yt_api_key_from_dict(search_args))
    search_args["key"] = os.getenv("YT_API_KEY")
    result = requests.get(base, params=search_args)
    return result

def youtube_api_get_videos(ids: list[str], base: str = "https://www.googleapis.com/youtube/v3/videos", **search_args):
    search_args["id"] = ','.join(ids)
    logger.info("Sending GET request to Youtube API /videos endpoint with: %s", strip_yt_api_key_from_dict(search_args))
    search_args["key"] = os.getenv("YT_API_KEY")
    result = requests.get(base, params=search_args).json()
    return result

def build_embed(video_ids: list[str]):
    logger.info("Building song choice embed...")
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
    logger.info("Embed successfully built.")
    return embed

def download_audio_from(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"
    opts = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "opus",
        }],
        "noplaylist": True,
        "outtmpl": "audio.%(ext)s",
        "overwrites": True,
    }
    logger.info("Starting audio download from %s", url)
    with yt_dlp.YoutubeDL(opts) as dl:
        dl.download(url)
    logger.info("Audio download complete")

class MusicPlayerCog(discord.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.slash_command()
    @discord.option("search", input_type=str)
    async def music(self: Self, ctx: discord.ApplicationContext, search: str):
        logger.info("Latency to command entrypoint is %f", self.bot.latency)
        response = youtube_api_search_with(part="snippet", maxResults=5, regionCode="SE", safeSearch="none", type="video", q=search)
        videos = response.json().get("items")
        video_ids = [video["id"]["videoId"] for video in videos]
        embed = build_embed(video_ids)
        await ctx.respond(embed=embed)

        def wait_for_valid_user_select(message: discord.Message):
            print(message.content)
            if message.author != ctx.author:
                return False
            try:
                selection = int(message.content)
            except ValueError:
                logger.info("Could not convert message content into integer.")
                return False
            valid_range = (1, len(video_ids))
            if not valid_range[0] <= selection <= valid_range[1]:
                logger.info("Selection is not within allowed range of numeric choices")
                return False
            return True
        
        try:
            message = await self.bot.wait_for("message", check=wait_for_valid_user_select, timeout=60.0)
            logger.info("Valid user selection {%s} encountered.", message.content)
        except asyncio.TimeoutError:
            logger.info("Music playback request has timed out.")
            await ctx.respond("Request timed out.")
            return

        selected_index = int(message.content) - 1
        selected_video = video_ids[selected_index]
        download_audio_from(selected_video)

def _main():
    dotenv.load_dotenv()

    intents = discord.Intents.default()
    intents.message_content = True
    bot = discord.Bot(intents=intents)
    bot.add_cog(MusicPlayerCog(bot))

    @bot.event
    async def on_ready():
        assert bot.user is not None, "bot.user was None"
        logger.info("Logged in as: %s (ID: %d)", bot.user.name, bot.user.id)

    # @bot.slash_command()
    # @discord.option("search", input_type=str)
    # async def music(ctx: discord.ApplicationContext, search: str):
    #     logger.info("Latency to command entrypoint is %f", bot.latency)
    #     response = youtube_api_search_with(part="snippet", maxResults=5, regionCode="SE", safeSearch="none", type="video", q=search)
    #     videos = response.json().get("items")
    #     video_ids = [video["id"]["videoId"] for video in videos]
    #     embed = build_embed(video_ids)
    #     await ctx.respond(embed=embed)

    #     def wait_for_valid_user_select(message: discord.Message):
    #         print(message.content)
    #         if message.author != ctx.author:
    #             return False
    #         try:
    #             selection = int(message.content)
    #         except ValueError:
    #             logger.info("Could not convert message content into integer.")
    #             return False
    #         valid_range = (1, len(video_ids))
    #         if not valid_range[0] <= selection <= valid_range[1]:
    #             logger.info("Selection is not within allowed range of numeric choices")
    #             return False
    #         return True
        
    #     try:
    #         message = await bot.wait_for("message", check=wait_for_valid_user_select, timeout=60.0)
    #         logger.info("Valid user selection {%s} encountered.", message.content)
    #     except asyncio.TimeoutError:
    #         logger.info("Music playback request has timed out.")
    #         await ctx.respond("Request timed out.")
    #         return

    #     selected_index = int(message.content) - 1
    #     selected_video = video_ids[selected_index]
    #     download_audio_from(selected_video)


    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    _main()