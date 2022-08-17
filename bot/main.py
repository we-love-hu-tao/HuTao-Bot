from vkbottle.bot import Bot
from vkbottle import load_blueprints_from_package
from variables import VK_TOKEN
from player_exists import PlayerExists
import create_pool
import asyncio


if __name__ == "__main__":
    bot = Bot(token=VK_TOKEN)

    for bp in load_blueprints_from_package("commands"):
        bp.load(bot)

    bot.labeler.message_view.register_middleware(PlayerExists)

    loop = asyncio.get_event_loop_policy().get_event_loop()
    loop.run_until_complete(create_pool.init())
    bot.run_forever()
