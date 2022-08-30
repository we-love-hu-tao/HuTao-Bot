from vkbottle.bot import Blueprint, Message
from player_exists import exists
from datetime import datetime
import drop
import create_pool
import json

bp = Blueprint("Characters list")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(text=["!персы", "!персонажи", "!мои персонажы"])
async def list_chatacters(message: Message):
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        """
        В базе данных будет ряд "characters" с типом jsonb, в котором будет
        список json'ов в таком виде:
        {
            "_type": "legendary_event_characters",
            "_id": 5,
            "date": 12525362,
            "const": 3,
            "exp": 6831,
            "weapon_type": "standard_weapon",
            "weapon_id": 1
        }
        _type - тип этого персонажа в drop.py
        _id - айди персонажа в этом типе
        date - дата выбивания персонажа
        const - созвездие, максимум 6, если оно больше - выдаются примогемы
        exp - думаю понятно
        weapon_type - тип оружия из drop.py, которое в данный момент у этого персонажа
        weapon_id - айди оружия из этого типа

        Также надо сделать базу данных артов ВСЕХ персонажей,
        когда игрок будет писать "!перс", у него должен появляться
        случайный арт из этой базы данных.

        Еще арты надо разделить на айди, что бы игрок мог выбрать
        любой арт из базы данных по его айди

        Как сделать базу данных картинок в вк - я пока не знаю
        """
        characters = await pool.fetchrow(
            "SELECT characters FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )

    characters = json.loads(characters["characters"])
    if len(characters) == 0:
        return "У вас еще нету персонажей! Их можно выбить в баннерах"

    new_msg = ""
    for character in characters:
        character_type = character["_type"]
        character_id = character["_id"]
        character_exp = character["exp"]

        drop_type = getattr(drop, character_type)
        for item in drop_type.items():
            if item[0] != "_type":
                if item[1]["_id"] == character_id:
                    name = item[0]
                    rarity = item[1]['rarity']

        new_msg += (
            f"Имя: {name}\n"
            f"Редкость: {rarity}\n"
            f"Опыт: {character_exp}\n"
            "------------------\n"
        )


    return new_msg


@bp.on.chat_message(text=("!перс <char_name>", "!персонаж <char_name>"))
async def character_info(message: Message, char_name):
    if not await exists(message):
        return

    pool = create_pool.pool
    async with pool.acquire() as pool:
        characters = await pool.fetchrow(
            "SELECT characters FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )

    char_info = None
    characters = json.loads(characters["characters"])
    for character in characters:
        character_type = character["_type"]
        character_id = character["_id"]

        drop_type = getattr(drop, character_type)
        for item in drop_type.items():
            if item[0] != "_type":
                if item[0].lower() == char_name.lower():
                    char_name = item[0]
                    char_info = character
                    break

    if char_info is None:
        return "Вы еще не выбили этого персонажа / его не существует!"

    drop_date = char_info["date"]
    constellation = char_info["const"]
    experience = char_info["exp"]

    drop_date = datetime.utcfromtimestamp(
        drop_date
    ).strftime('%H:%M:%S - %d-%m-%Y')

    return (
        f"Имя персонажа: {char_name}\n"
        f"Дата получения: {drop_date}\n"
        f"Созвездие: {constellation}\n"
        f"Опыт: {experience}"
    )


