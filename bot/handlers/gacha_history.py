from datetime import datetime
from typing import Literal, Union

import msgspec
from loguru import logger
from vkbottle import Callback, GroupEventType, Keyboard, KeyboardButtonColor
from vkbottle.bot import BotLabeler, Message, MessageEvent, rules

import create_pool
from utils import (check_item_type, color_to_rarity, exists, get_avatar_data,
                   get_text_map, get_weapon_data, resolve_id, resolve_map_hash)

bl = BotLabeler()
bl.vbml_ignore_case = True

weapons_type = [
    "normal_standard_weapons", "rare_standard_weapons", "legendary_standard_weapons"
]
characters_type = [
    "rare_standard_characters", "legendary_standard_characters", "legendary_event_characters"
]


def filter_records(records, gacha_type: int):
    """Filters records by gacha type"""
    new_records = []
    for record in records:
        if record['gacha_type'] == gacha_type:
            new_records.append(record)

    # Reversing records, because for some reason
    # first record is the first dropped item
    new_records.reverse()
    return new_records


async def get_last_history(
    pool,
    message: Union[Message, MessageEvent],
    gacha_type,
    offset: int = 0
):
    if isinstance(message, Message):
        user_id = message.from_id
        peer_id = message.peer_id
    else:
        user_id = message.object.user_id
        peer_id = message.object.peer_id

    records = await pool.fetchrow(
        "SELECT gacha_records FROM players WHERE user_id=$1 AND peer_id=$2",
        user_id, peer_id
    )
    records = msgspec.json.decode(records['gacha_records'].encode("utf-8"))
    records = filter_records(records, gacha_type)

    if len(records) > 0:
        if offset > 0:
            records = records[offset:offset+5]
        else:
            records = records[:5]

    return records


async def raw_history_to_normal(records: list[dict]):
    """Formats history to make it human-readable"""
    text_map = await get_text_map()
    weapon_data = await get_weapon_data()
    avatar_data = await get_avatar_data()

    history = ""
    for roll in records:
        drop_time = roll['time']
        drop_time = datetime.fromtimestamp(
            drop_time
        ).strftime('%H:%M:%S - %d-%m-%Y')

        item_info = resolve_id(roll['item_id'], avatar_data, weapon_data)
        if item_info is None:
            logger.error(f"Unknown drop in history: {roll['item_id']}")
            continue
        drop_name = resolve_map_hash(text_map, item_info.name_text_map_hash)

        if drop_name is None:
            drop_name = "Неизвестный предмет"

        if check_item_type(item_info.id) == 0:
            # Avatar
            drop_rarity = color_to_rarity(item_info.quality)
            drop_emoji = "&#129485;"
        else:
            # Weapon
            drop_rarity = item_info.rank
            drop_emoji = "&#128481;"

        history += (
            f"{drop_emoji} {drop_name} {'&#11088;' * drop_rarity}\n"
            f"Время: {drop_time} (GMT+3)\n"
            "-------------\n"
        )
    return history


def generate_move_keyboard(
    gacha_type: int,
    direction: Literal['forward', 'back', 'both'],
    offset: int = 0
):
    """Generates keyboard to move forward or back in history"""
    if direction == "forward":
        direction_text = "Вперед"
        button_color = KeyboardButtonColor.POSITIVE
    elif direction == "back":
        direction_text = "Назад"
        button_color = KeyboardButtonColor.NEGATIVE
    else:
        return (
            Keyboard(one_time=False, inline=True)
            .add(Callback(
                "Назад",
                payload={
                    "gacha_type": gacha_type,
                    "direction": "back",
                    "offset": offset
                }),
                color=KeyboardButtonColor.NEGATIVE)
            .add(Callback(
                "Вперед",
                payload={
                    "gacha_type": gacha_type,
                    "direction": "forward",
                    "offset": offset
                }),
                color=KeyboardButtonColor.POSITIVE)
            .get_json()
        )
    keyboard = (
        Keyboard(one_time=False, inline=True)
        .add(Callback(
            direction_text,
            payload={
                "gacha_type": gacha_type,
                "direction": direction,
                "offset": offset
            }),
            color=button_color)
        .get_json()
    )
    return keyboard


@bl.message(text="!история")
async def gacha_history(message: Message):
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        gacha_type = await pool.fetchrow(
            "SELECT current_banner FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )
        gacha_type = gacha_type['current_banner']
        raw_history = await get_last_history(pool, message, gacha_type)
    logger.info(raw_history)

    if raw_history is None or len(raw_history) == 0:
        return "В выбранном вами баннере вы еще ничего не выбивали!"

    history = await raw_history_to_normal(raw_history)
    keyboard = generate_move_keyboard(gacha_type, "forward")
    await message.answer(history, keyboard=keyboard)


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadMapRule([
        ("gacha_type", int),
        ("direction", str),
        ("offset", int)
    ])
)
async def gacha_history_move(event: MessageEvent):
    pool = create_pool.pool
    payload = event.get_payload_json()
    gacha_type = payload['gacha_type']
    direction = payload['direction']
    offset = payload['offset']

    if direction == "forward":
        offset += 5
    elif direction == "back":
        if offset > 0:
            offset -= 5
        else:
            keyboard = generate_move_keyboard(gacha_type, "forward", -5)
            await event.edit_message(
                "Вы не можете посмотреть, что вам выпадет в будущем!", keyboard=keyboard
            )
            return

    async with pool.acquire() as pool:
        raw_history = await get_last_history(pool, event, gacha_type, offset)

    if raw_history is None or len(raw_history) == 0:
        keyboard = generate_move_keyboard(gacha_type, "back", offset)
        await event.edit_message("В это время вы ничего не выбивали!", keyboard=keyboard)
        return
    else:
        logger.debug(raw_history)
        history = await raw_history_to_normal(raw_history)

    keyboard = generate_move_keyboard(gacha_type, "both", offset)

    await event.edit_message(history, keyboard=keyboard)
