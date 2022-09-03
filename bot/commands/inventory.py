from vkbottle.bot import Blueprint, Message
from player_exists import exists
from utils import get_drop
# from loguru import logger
import create_pool
import json
import drop

bp = Blueprint("Use wish")
bp.labeler.vbml_ignore_case = True


def format_inventory(inventory: dict, rarity: int = 5):
    new_message = f"Оружия ({'&#11088;' * rarity}):\n"
    for item in inventory:
        if item['rarity'] != rarity:
            continue
        item_count = item['count']
        item_name = None
        if item['item_type'] == "weapon":
            weapon_type = item['weapon']['_type']
            weapon_id = item['weapon']['_id']

            drop_type = getattr(drop, weapon_type)
            weapon = get_drop(drop_type, weapon_id)

            item_name = weapon['drop_name']

        if item == inventory[-1]:
            ending = "."
        else:
            ending = ", "
        new_message += f"{item_name} (x{item_count}){ending}"

    if new_message == f"Оружия ({'&#11088;' * rarity}):\n":
        new_message += "Пока пусто!"
    return new_message


@bp.on.chat_message(text=("!инвентарь", "!инв"))
async def inventory_handler(message: Message):
    if not await exists(message):
        return

    """
    inventory: jsonb
    [
        {
            "item_type": "weapon",
            "rarity": 3,
            "count": 1,
            "date": 1662204715,
            "weapon": {
                "_type": "normal_standard_weapons",
                "_id": 7,
                "exp": 1,
                "asc": 1,
            }
        },
    ]
    """

    pool = create_pool.pool
    async with pool.acquire() as pool:
        inventory = await pool.fetchrow(
            "SELECT inventory FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )
    inventory = json.loads(inventory['inventory'])

    if len(inventory) == 0:
        return "Ваш инвентарь пустой!"

    five_stars = format_inventory(inventory)
    four_stars = format_inventory(inventory, 4)
    new_msg = f"{five_stars}\n\n{four_stars}"

    return new_msg
