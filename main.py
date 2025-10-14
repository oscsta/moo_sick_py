import dotenv
import os
import logging

from bot import MooSick

def setup_logging():
    logging.basicConfig(level=logging.INFO)

def main():
    dotenv.load_dotenv()
    setup_logging()

    bot = MooSick()
    bot.run(os.getenv("DISCORD_API_KEY"))

if __name__ == "__main__":
    main()