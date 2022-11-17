import asyncio
from os import mkdir, path

from loguru import logger
from vkbottle import Bot

import create_pool
from handlers import labelers
from config import VK_GROUP_TOKEN

# TODO: Image generation (wishes)

if __name__ == "__main__":
    log_path = "logs/"
    if not path.exists(log_path):
        mkdir(log_path)
    logger.add("logs/file_{time}.log", level="INFO", rotation="10 MB")

    bot = Bot(token=VK_GROUP_TOKEN)
    logger.info(labelers)

    for custom_labeler in labelers:
        bot.labeler.load(custom_labeler)

    # Create asyncpg pool
    loop = asyncio.get_event_loop_policy().get_event_loop()
    loop.run_until_complete(create_pool.init())

    # Run bot
    bot.run_forever()

