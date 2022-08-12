from vkbottle.bot import Blueprint, Message
from player_exists import exists
import create_pool

bp = Blueprint("Characters list")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(text=["!персы", "!персонажи", "!мои персонажы"])
async def list_chatacters(message: Message):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        if not await exists(message, pool):
            return

    """
    В базе данных будет ряд "characters" с типом jsonb, в котором будет
    список json'ов в таком виде:
    {
        "type": "legendary_event_characters",
        "char_id": 5,
        "exp": 6831,
        "weapon_type": "standard_weapon",
        "weapon_id": 1
    }
    type - тип этого персонажа в drop.py
    char_id - айди персонажа в этом типе
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

    return "В разработке!"
