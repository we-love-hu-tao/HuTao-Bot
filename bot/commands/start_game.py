from vkbottle.bot import Blueprint, Message
import asyncpg
import random

bp = Blueprint("Start command")
bp.labeler.vbml_ignore_case = True

NAMES = (
    "Люмин", "Итэр", "Ху Тао",
    "Кэ Цин", "Эмбер", "Чжун Ли",
    "Янь Фей", "Ноэлль", "Барбара",
    "Венти", "Эола", "Лиза ( ͡° ͜ʖ ͡°)",
    "Кокоми", "Ци Ци", "Дилюк",
    "Тимми (🏹 ---> 🕊)", "Райдэн",
    "Тарталья", "Тома", "Шэнь Хэ",
    "Яэ Мико", "Хиличурл", "Маг бездны",
    "Фишль", "Гань Юй", "Паймон",
    "Путешественник", "СтасБарецкий228",
    "Ваша жаба", "Дед", "Буба",
    "Кокосовая коза", "чича"
    "Консерва", "мда", "кринж",
    "амогус", "сус", "сырник",
    "0); DROP DATABASE users; --",
    "Null Null", "c6 Ху Тао", "донатер",
    "Богдан"
)


@bp.on.message(text="!начать")
async def standard_wish(message: Message):
    async with asyncpg.create_pool(
        user="postgres", database="genshin_bot", passfile="pgpass.conf"
    ) as pool:
        async with pool.acquire() as db:
            is_exists = await db.fetchrow(
                "SELECT user_id FROM players WHERE user_id=$1 AND peer_id=$2",
                message.from_id, message.peer_id
            )
            if is_exists is not None:
                await message.answer("Вы уже зашли в Genshin Impact")
            else:
                await db.execute(
                    "INSERT INTO players (user_id, peer_id, nickname) VALUES "
                    "($1, $2, $3)",
                    message.from_id, message.peer_id, random.choice(NAMES)
                )
                await message.answer(
                    "Вы зашли в Genshin Impact!\n"
                    "Напишите !персонаж, что бы увидеть ваш никнейм "
                    "и количество молитв"
                )
