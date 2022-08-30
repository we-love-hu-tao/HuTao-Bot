from vkbottle.bot import Bot
from vkbottle import load_blueprints_from_package
from variables import VK_GROUP_TOKEN
from loguru import logger
from os import path, mkdir
import create_pool
import asyncio

# TODO: Генерация изображений с нуля;
# TODO: Описание предметов (можно попробовать
# TODO: использовать какое-нибудь апи / брать с вики по геншину)

if __name__ == "__main__":
    bot = Bot(token=VK_GROUP_TOKEN)

    for bp in load_blueprints_from_package("commands"):
        bp.load(bot)

    loop = asyncio.get_event_loop_policy().get_event_loop()
    loop.run_until_complete(create_pool.init())

    log_path = ".logs/"
    if not path.exists(log_path):
        mkdir(log_path)
    logger.add("logs/file_{time}.log")

    bot.run_forever()
