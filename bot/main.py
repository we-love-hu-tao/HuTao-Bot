import asyncio
from os import makedirs

from aiohttp.client_exceptions import ClientOSError
from loguru import logger
from vkbottle import Bot

import create_pool
from handlers import labelers
from config import VK_GROUP_TOKEN

# TODO: Image generation (wishes)

if __name__ == "__main__":
    log_path = "logs"
    error_path = "logs/errors"
    generation_path = "generated_imgs"  # Don't change
    makedirs(log_path, exist_ok=True)
    makedirs(error_path, exist_ok=True)
    makedirs(generation_path, exist_ok=True)

    logger.add(f"{log_path}/file_{{time}}.log", level="INFO", rotation="100 MB")
    logger.add(f"{error_path}/file_{{time}}.log", level="ERROR", rotation="100 MB")

    bot = Bot(token=VK_GROUP_TOKEN)

    for custom_labeler in labelers:
        bot.labeler.load(custom_labeler)

    @bot.error_handler.register_error_handler(ClientOSError)
    async def no_internet_error_handler(e: ClientOSError):
        logger.warning(f"No internet connection: {e}")

    # Create asyncpg pool
    loop = asyncio.get_event_loop_policy().get_event_loop()
    loop.run_until_complete(create_pool.init())

    # Run bot
    bot.run_forever()

