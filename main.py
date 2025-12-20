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

def youtube_api_get_video_info(ids: list[str], base: str = "https://www.googleapis.com/youtube/v3/videos", **search_args):
    search_args["id"] = ','.join(ids)
    logger.info("Sending GET request to Youtube API /videos endpoint with: %s", strip_yt_api_key_from_dict(search_args))
    search_args["key"] = os.getenv("YT_API_KEY")
    result = requests.get(base, params=search_args).json()
    return result

def build_embed(video_ids: list[str]):
    logger.info("Building song choice embed...")
    video_info_list = youtube_api_get_video_info(video_ids, part="snippet,contentDetails", regionCode="SE")
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
    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.bot = bot
        self.queue = []

    @discord.slash_command(guild_ids=[123475953098686464])
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
        self.queue.append(selected_video)

        if ctx.voice_client is None:
            if invoker_voice := ctx.author.voice:
                await invoker_voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)


        
    @discord.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        voice_client = member.guild.voice_client
        if voice_client and before.channel == voice_client.channel and after.channel != voice_client.channel:
            human_members = [m for m in voice_client.channel.members if not m.bot]
            if len(human_members) == 0:
                self.music_cog_cleanup()
                await voice_client.disconnect()
                # TODO: Cleanup logic for music player

    def on_audio_finish(self, error, ctx: discord.ApplicationContext):
        self.bot.loop.create_task(self.play_next(ctx))

    async def play_next(self, ctx: discord.ApplicationContext):
        if not self.queue:
            return
        video_id = self.queue.pop(0)
        if ctx.voice_client is None or ctx.voice_client.is_playing():
            return
        download_audio_from(video_id)
        ctx.voice_client.play(
            discord.FFmpegOpusAudio("audio.opus"),
            after=lambda error: self.on_audio_finish(error, ctx),
        )

    def music_cog_cleanup(self):
        self.queue.clear()

    @discord.slash_command(guild_ids=[123475953098686464])
    async def skip(self: Self, ctx: discord.ApplicationContext):
        if not ctx.voice_client:
            return
        logger.info("Skipping current playback with voice_client.stop()")
        ctx.voice_client.stop()
        await ctx.respond("Skipped current playback.")


def _main():
    dotenv.load_dotenv()

    intents = discord.Intents.all()
    intents.message_content = True
    intents.voice_states = True
    bot = discord.Bot(intents=intents)
    bot.add_cog(MusicPlayerCog(bot))

    @bot.event
    async def on_ready():
        assert bot.user is not None, "bot.user was None"
        logger.info("Logged in as: %s (ID: %d)", bot.user.name, bot.user.id)

    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    _main()