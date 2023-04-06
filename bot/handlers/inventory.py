from vkbottle.bot import BotLabeler, Message

from utils import (
    exists, get_inventory, get_textmap, get_weapon_data, resolve_id,
    resolve_map_hash
)

bl = BotLabeler()
bl.vbml_ignore_case = True


async def format_inventory(inventory: list[dict], rarity: int = 5):
    """Formats inventory to make it human-readable"""
    weapon_data = await get_weapon_data()
    textmap = await get_textmap()
    new_message = f"Оружия ({'&#11088;' * rarity}):\n"
    for item in inventory:
        if item['item_type'] != "ITEM_WEAPON":
            continue

        item_excel = resolve_id(item['id'], weapon_data=weapon_data)
        item_rarity = item_excel['rankLevel']

        if item_rarity != rarity:
            continue

        item_name = resolve_map_hash(textmap, item_excel['nameTextMapHash'])
        item_count = item['count']

        if item == inventory[-1]:
            ending = "."
        else:
            ending = ", "
        new_message += f"{item_name} (x{item_count}){ending}"

    if new_message == f"Оружия ({'&#11088;' * rarity}):\n":
        new_message += "Пока пусто!"
    return new_message


@bl.message(text=("!инвентарь", "!инв"))
async def inventory_handler(message: Message):
    if not await exists(message):
        return

    """
    inventory: jsonb
    [
        {
            "item_type": "ITEM_WEAPON",
            "id": 11101,
            "count": 1
        },
    ]
    """
    inventory = await get_inventory(message.from_id, message.peer_id)

    if len(inventory) == 0:
        return "Ваш инвентарь пустой!"

    five_stars = await format_inventory(inventory)
    four_stars = await format_inventory(inventory, 4)
    three_stars = await format_inventory(inventory, 3)
    new_msg = f"{five_stars}\n\n{four_stars}\n\n{three_stars}"

    return new_msg
