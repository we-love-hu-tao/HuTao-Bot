from vkbottle.bot import Blueprint, Message
from player_exists import exists
import asyncpg
import drop
import json

bp = Blueprint("Gacha History")
bp.labeler.vbml_ignore_case = True


@bp.on.message(text="!история <banner_type>")
async def gacha_history(message: Message, banner_type):
    async with asyncpg.create_pool(
        user="postgres", database="genshin_bot", passfile="pgpass.conf"
    ) as pool:
        async with pool.acquire() as db:
            if not await exists(message, db):
                return

            await db.set_type_codec(
                'json',
                encoder=json.dumps,
                decoder=json.loads,
                schema='pg_catalog'
            )

            if banner_type == "ивент":
                raw_history = await db.fetchrow(
                    "SELECT event_rolls_history FROM players WHERE user_id=$1 AND peer_id=$2",
                    message.from_id, message.peer_id
                )
                history_type = "event_rolls_history"
            elif banner_type == "стандарт":
                raw_history = await db.fetchrow(
                    "SELECT standard_rolls_history FROM players WHERE user_id=$1 AND peer_id=$2",
                    message.from_id, message.peer_id
                )
                history_type = "standard_rolls_history"
            else:
                await message.answer("Но такого типа баннера не существует (пока что)!")
                return

            raw_history = json.loads(raw_history[history_type])
            if len(raw_history) > 0:
                history = ""
                for roll in raw_history:
                    print(roll)
                    # name =
                    pulled_time = roll["time"]
                    history += f"Время: {pulled_time}\n"
            else:
                await message.answer("Вы еще ничего не выбивали!")
                return

            print(raw_history)
            await message.answer(history)
