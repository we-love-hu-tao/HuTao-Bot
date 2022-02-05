from vkbottle.bot import Message, Blueprint
import genshinstats as gs
import json
import asyncio


bp = Blueprint("UserStats")


with open("config.json", "r") as file:
    config = json.load(file)
gs.set_cookie(ltuid=config["ltuid"], ltoken=config["ltoken"])


@bp.on.message(text="<prefix>перс <genshin_id:int>")
async def userstats(message: Message, genshin_id):

    data = await asyncio.to_thread(gs.get_user_stats, genshin_id)
    data = data["stats"]

    achives = data["achievements"]
    characters = data["characters"]
    days = data["active_days"]
    bezdna = data["spiral_abyss"]

    await message.answer(
        f'Достижений: {achives}\n'
        f'Всего персонажей: {characters}\n'
        f'Активных дней: {days}\n'
        f'Этаж Бездны: {bezdna}\n'
    )
