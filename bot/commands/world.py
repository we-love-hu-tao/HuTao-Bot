from vkbottle.bot import Blueprint, Message
import genshinstats as gs
import json
import asyncio

bp = Blueprint("world")

with open("config.json", "r") as file:
    config = json.load(file)
gs.set_cookie(ltuid=config["ltuid"], ltoken=config["ltoken"])


@bp.on.message(text="!мир <genshin_id:int>")
async def world_handler(message: Message, genshin_id: int):
    data = await asyncio.to_thread(gs.get_user_stats, genshin_id)
    data = data['stats']
    await message.answer(
        f"Анемокулы: {data['anemoculi']}\n"
        f"Геокулы: {data['geoculi']}\n"
        f"Электрокулы: {data['electroculi']}\n"
        f"Обычные сундуки: {data['common_chests']}\n"
        f"Богатые сундуки: {data['exquisite_chests']}\n"
        f"Драгоценные сундуки: {data['precious_chests']}\n"
        f"Роскошные сундуки: {data['luxurious_chests']}\n"
        f"Телепортаторы: {data['unlocked_waypoints']}\n"
        f"Данжи: {data['unlocked_domains']}"
    )
