from vkbottle.bot import Blueprint, Message, MessageEvent, rules
from vkbottle import (
    Keyboard,
    KeyboardButtonColor,
    Callback,
    GroupEventType
)
from datetime import datetime
from typing import Literal
from player_exists import exists
import create_pool
import json
import drop

bp = Blueprint("Gacha History")
bp.labeler.vbml_ignore_case = True

weapons_type = [
    "normal_standard_weapons", "rare_standard_weapons", "legendary_standard_weapons"
]
characters_type = [
    "rare_standard_characters", "legendary_standard_characters", "legendary_event_characters"
]


async def get_last_history(
    pool, message: Message, banner_type: Literal["standard", "event"], last: int = 5
):
    history_type = f"{banner_type}_rolls_history"

    raw_history = await pool.fetchrow(
        f"SELECT {history_type} FROM players WHERE user_id=$1 AND peer_id=$2",
        message.from_id, message.peer_id
    )
    return json.loads(raw_history[history_type])[-last:]


@bp.on.chat_message(text="!история <banner_type>")
async def gacha_history(message: Message, banner_type: Literal["стандарт", "ивент"]):
    if not exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        if banner_type == "стандарт":
            banner_type = "standard"
            raw_history = await get_last_history(pool, message, banner_type)
        elif banner_type == "ивент":
            banner_type = "event"
            raw_history = await get_last_history(pool, message, banner_type)
        else:
            return "Но такого типа баннера не существует (пока что)!"

    if len(raw_history) > 0:
        history = "Последние 5 дропов:\n"
        print(raw_history)
        for roll in raw_history:
            drop_type = getattr(drop, roll["type"])
            for item in drop_type.items():
                if item[0] != "_type":
                    if item[1]["_id"] == roll["item_id"]:
                        name = item[0]
                        break

            drop_type = roll["type"]

            drop_emoji = ""
            if drop_type in weapons_type:
                drop_emoji = "&#128481;"
            elif drop_type in characters_type:
                drop_emoji = "&#129485;"

            pulled_time = datetime.utcfromtimestamp(
                roll["time"]
            ).strftime('%H:%M:%S - %d-%m-%Y')
            history += (
                f"{drop_emoji} {name}\n"
                f"Время: {pulled_time} (GMT+3)\n"
                "-------------\n"
            )
    else:
        return "Вы еще ничего не выбивали!"

    keyboard = (
        Keyboard(one_time=False, inline=True)
        .add(Callback("Назад", payload={"banner_type": banner_type, "direction": "back", "offset": 0}), color=KeyboardButtonColor.NEGATIVE)
        .add(Callback("Вперед", payload={"banner_type": banner_type, "direction": "forward", "offset": 0}), color=KeyboardButtonColor.POSITIVE)
        .get_json()
    )
    await message.answer(history, keyboard=keyboard)


@bp.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadMapRule([
        ("banner_type", str),
        ("direction", str),
        ("offset", int)
    ])
)
async def gacha_history_forward(event: MessageEvent):
    pool = create_pool.pool
    banner_type = event.get_payload_json()["banner_type"]
    async with pool.acquire() as pool:
        raw_history = await get_last_history(pool, event, banner_type, 10)  # ! AttributeError: 'MessageEventMin' object has no attribute 'from_id'

    if len(raw_history) > 0:
        history = "Последние 10 дропов:\n"              
        for roll in raw_history:
            drop_type = getattr(drop, roll["type"])
            for item in drop_type.items():
                if item[0] != "_type":
                    if item[1]["_id"] == roll["item_id"]:
                        name = item[0]
                        break

            drop_type = roll["type"]

            drop_emoji = ""
            if drop_type in weapons_type:
                drop_emoji = "&#128481;"
            elif drop_type in characters_type:
                drop_emoji = "&#129485;"
            pulled_time = datetime.utcfromtimestamp(
                roll["time"]
            ).strftime('%H:%M:%S - %d-%m-%Y')
            history += (
                f"{drop_emoji} {name}\n"
                f"Время: {pulled_time} (GMT+3)\n"
                "-------------\n"
            )
    else:
        event.edit_message("Вы еще ничего не выбивали!")

    await event.edit_message(history)
