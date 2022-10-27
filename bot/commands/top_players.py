from vkbottle.bot import Blueprint, Message

from utils import exists

"""
import create_pool
from item_names import ADVENTURE_EXP, PRIMOGEM
from utils import exists, exp_to_level, get_item
"""

bp = Blueprint("Top players")
bp.labeler.vbml_ignore_case = True

# Currently, I have no idea, how to implement top of players
# with new inventory/gacha system, so, yeah...


@bp.on.chat_message(text=("!топ", "!топ <top_type>"))
async def top_players_handler(message: Message, top_type=None):
    if not await exists(message):
        return
    return "Топ вернется в будущем!"

'''
@bp.on.chat_message(text=("!топ", "!топ <top_type>"))
async def top_players_handler(message: Message, top_type=None):
    if not await exists(message):
        return
    pool = create_pool.pool

    if top_type is not None:
        if len(top_type.split()) > 1:
            top_type = top_type.split()[0]

    async with pool.acquire() as pool:
        new_msg = ""
        top_number = 1
        # TODO: rolls top
        """
        elif top_type == "крутки":
            if add_param in STANDARD_VARIANTS or add_param is None:
                top_players = await pool.fetch(
                    "SELECT total_standard_rolls, nickname FROM players "
                    "ORDER BY total_standard_rolls DESC LIMIT 10"
                )
            elif add_param in EVENT_VARIANTS:
                top_players = await pool.fetch(
                    "SELECT total_event_rolls, nickname FROM players "
                    "ORDER BY total_event_rolls DESC LIMIT 10"
                )

            for player in top_players:
                new_msg += (
                    f"{top_number}. Откручено: {player[0]} | "
                    f"{player['nickname']}\n"
                )
                top_number += 1
        """
        if top_type is None:
            top_players = await pool.fetch(
                "SELECT nickname, inventory FROM players"
            )

            top_primogems = []
            for player in top_players:
                primogems = await get_item(
                    PRIMOGEM, inventory=top_players['inventory']
                )
                top_primogems.append((primogems['count'], player['nickname']))
                primogems = primogems['count']
                new_msg += (
                    f"{top_number}. Примогемы: {player['primogems']} | "
                    f"{player['nickname']}\n"
                )
                top_number += 1
        elif top_type == "уровень":
            top_players = await pool.fetch(
                "SELECT user_id, peer_id, nickname FROM players "
            )

            for player in top_players:
                exp = await get_item(
                    ADVENTURE_EXP, top_players['user_id'], top_players['peer_id']
                )
                level = exp_to_level(exp['count'])
                new_msg += (
                    f"{top_number}. Уровень: {exp_to_level(player['experience'])} | "
                    f"{player['nickname']}\n"
                )
                top_number += 1
        else:
            return "Такого топа не существует (пока что)!"

    return new_msg
'''
