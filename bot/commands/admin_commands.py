from vkbottle.bot import Blueprint, Message
import asyncpg

bp = Blueprint("Admin")
bp.labeler.vbml_ignore_case = True

admin_list = (322615766,)


@bp.on.message(text="!гнш бан <mention>")
async def ban_user(message: Message, mention):
    if message.from_id in admin_list:
        mention_id = int(mention.split("|")[0][1:].replace("id", ""))
        async with asyncpg.create_pool(
            user="postgres", database="genshin_bot", passfile="pgpass.conf"
        ) as pool:
            async with pool.acquire() as db:
                is_exists = await db.fetchrow(
                    "SELECT user_id FROM banned WHERE user_id=$1",
                    mention_id
                )
                if is_exists is None:
                    await db.execute(
                        "UPDATE banned SET banned=$1 WHERE user_id=$2",
                        True, mention_id,
                    )
                    await message.answer(
                        "этот человек совершил что-то ужасное, поэтому был забанен"
                    )
                else:
                    await message.answer("этот человек уже забанен")
