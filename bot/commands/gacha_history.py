from vkbottle.bot import Blueprint, Message, MessageEvent, rules
from vkbottle import (
    Keyboard,
    KeyboardButtonColor,
    Callback,
    GroupEventType
)
from datetime import datetime
from typing import Union, Literal
from player_exists import exists
from loguru import logger
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
    pool,
    message: Union[Message, MessageEvent],
    banner_type: Literal["standard", "event"],
    offset: int = 0
):
    history_type = f"{banner_type}_rolls_history"

    if type(message) == Message:
        user_id = message.from_id
        peer_id = message.peer_id
    elif type(message) == MessageEvent:
        user_id = message.object.user_id
        peer_id = message.object.peer_id

    raw_history = await pool.fetchrow(
        f"SELECT {history_type} FROM players WHERE user_id=$1 AND peer_id=$2",
        user_id, peer_id
    )
    if raw_history is not None:
        if offset > 0:
            raw_history = json.loads(raw_history[history_type])[offset:offset+offset]
        else:
            raw_history = json.loads(raw_history[history_type])[:5]

    return raw_history


async def raw_history_to_normal(raw_history: dict):
    if len(raw_history) > 0:
        history = ""
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
        return
    return history


@bp.on.chat_message(text="!история <banner_type>")
async def gacha_history(message: Message, banner_type: Literal["стандарт", "ивент"]):
    if not await exists(message):
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

    history = await raw_history_to_normal(raw_history)

    if history is None:
        return "Вы еще ничего не выбивали!"
    else:
        history = "Последние 5 дропов:\n"+history

    keyboard = (
        Keyboard(one_time=False, inline=True)
        .add(Callback(
            "Вперед",
            payload={
                "banner_type": banner_type,
                "direction": "forward",
                "offset": 0
            }),
            color=KeyboardButtonColor.POSITIVE)
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
async def gacha_history_move(event: MessageEvent):
    pool = create_pool.pool
    payload = event.get_payload_json()
    banner_type = payload["banner_type"]
    direction = payload["direction"]
    offset = payload["offset"]

    if direction == "forward":
        offset += 5
        logger.debug("--------------")
        logger.debug(f"Current offset: {offset}")
        logger.debug("--------------")
    elif direction == "back":
        logger.debug("--------------")
        logger.debug(f"Current offset (back): {offset-5}")
        logger.debug("--------------")
        if offset > 0:
            offset -= 5
        else:
            keyboard = (
                Keyboard(one_time=False, inline=True)
                .add(Callback(
                    "Вперед",
                    payload={
                        "banner_type": banner_type,
                        "direction": "forward",
                        "offset": 0
                    }),
                    color=KeyboardButtonColor.POSITIVE)
                .get_json()
            )
            await event.edit_message(
                "Вы не можете посмотреть, что вам выпадет в будущем!", keyboard=keyboard
            )
            return

    async with pool.acquire() as pool:
        raw_history = await get_last_history(pool, event, banner_type, offset)

    if raw_history is None or len(raw_history) == 0:
        keyboard = (
            Keyboard(one_time=False, inline=True)
            .add(Callback(
                "Назад",
                payload={
                    "banner_type": banner_type,
                    "direction": "back",
                    "offset": offset
                }),
                color=KeyboardButtonColor.NEGATIVE)
            .get_json()
        )
        await event.edit_message("В это время вы ничего не выбили!", keyboard=keyboard)
        return
    else:
        logger.debug(raw_history)
        history = await raw_history_to_normal(raw_history)
        history = "5 дропов:\n"+history

    keyboard = (
            Keyboard(one_time=False, inline=True)
            .add(Callback(
                "Назад",
                payload={
                    "banner_type": banner_type,
                    "direction": "back",
                    "offset": offset
                }),
                color=KeyboardButtonColor.NEGATIVE)
            .add(Callback(
                "Вперед",
                payload={
                    "banner_type": banner_type,
                    "direction": "forward",
                    "offset": offset
                }),
                color=KeyboardButtonColor.POSITIVE)
            .get_json()
        )

    await event.edit_message(history, keyboard=keyboard)
