from vkbottle.bot import Bot
from vkbottle import load_blueprints_from_package
import json


with open("config.json", "r") as file:
    config = json.load(file)

bot = Bot(token=config["bot_token"])

for bp in load_blueprints_from_package("commands"):
    bp.load(bot)

bot.run_forever()
