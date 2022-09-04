from vkbottle.bot import Blueprint, Message
from player_exists import exists
from variables import EVENT_VARIANTS, STANDARD_VARIANTS
from utils import exp_to_level
import create_pool

bp = Blueprint("Top players")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(text=("!топ", "!топ <top_type>"))
async def top_players_handler(message: Message, top_type=None):
    if not await exists(message):
        return
    pool = create_pool.pool

    add_param = None
    if top_type is not None:
        if len(top_type.split()) > 1:
            add_param = top_type.split()[1]
            top_type = top_type.split()[0]

    async with pool.acquire() as pool:
        new_msg = ""
        top_number = 1
        if top_type is None:
            top_players = await pool.fetch(
                "SELECT primogems, nickname FROM players ORDER BY primogems DESC LIMIT 10"
            )

            for player in top_players:
                new_msg += (
                    f"{top_number}. Примогемы: {player['primogems']} | "
                    f"{player['nickname']}\n"
                )
                top_number += 1
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
        elif top_type == "уровень":
            top_players = await pool.fetch(
                "SELECT experience, nickname FROM players "
                "ORDER BY experience DESC LIMIT 10"
            )

            for player in top_players:
                new_msg += (
                    f"{top_number}. Уровень: {exp_to_level(player['experience'])} | "
                    f"{player['nickname']}\n"
                )
                top_number += 1
        else:
            return "Такого топа не существует (пока что)!"

    return new_msg
