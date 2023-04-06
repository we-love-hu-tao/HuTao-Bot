from os import makedirs

from aiohttp.client_exceptions import ClientOSError
from loguru import logger
from vkbottle.bot import Bot

import create_pool
from config import VK_GROUP_TOKEN
from handlers import labelers

# TODO: Image generation (wishes)

if __name__ == "__main__":
    log_path = "logs"
    error_path = "logs/errors"
    generation_path = "generated_imgs"  # Don't change
    banners_cache = "banners_cache"  # Also don't change
    makedirs(log_path, exist_ok=True)
    makedirs(error_path, exist_ok=True)
    makedirs(generation_path, exist_ok=True)
    makedirs(banners_cache, exist_ok=True)

    logger.add(f"{log_path}/file_{{time}}.log", level="INFO", rotation="100 MB")
    logger.add(f"{error_path}/file_{{time}}.log", level="ERROR", rotation="100 MB")

    bot = Bot(token=VK_GROUP_TOKEN)

    for custom_labeler in labelers:
        bot.labeler.load(custom_labeler)

    @bot.error_handler.register_error_handler(ClientOSError)
    async def no_internet_error_handler(e: ClientOSError):
        logger.warning(f"No internet connection: {e}")

    # Create asyncpg pool on bot startup
    bot.loop_wrapper.on_startup.append(create_pool.init())

    # Run bot
    bot.run_forever()
