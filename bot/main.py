from vkbottle.bot import Bot
from vkbottle import load_blueprints_from_package
from config import VK_GROUP_TOKEN
from loguru import logger
from os import path, mkdir
import create_pool
import asyncio

# TODO: Image generation (wishes, banners)

if __name__ == "__main__":
    log_path = "logs/"
    if not path.exists(log_path):
        mkdir(log_path)
    logger.add("logs/file_{time}.log", level="INFO", rotation="10 MB")

    bot = Bot(token=VK_GROUP_TOKEN)

    for bp in load_blueprints_from_package("commands"):
        bp.load(bot)

    loop = asyncio.get_event_loop_policy().get_event_loop()
    loop.run_until_complete(create_pool.init())

    bot.run_forever()
