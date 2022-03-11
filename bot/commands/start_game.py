from vkbottle.bot import Blueprint, Message
import aiosqlite
import random

bp = Blueprint("Start command")
bp.labeler.vbml_ignore_case = True

NAMES = (
    "Люмин", "Итэр", "Ху Тао",
    "Кэ Цин", "Эмбер", "Чжун Ли",
    "Янь Фей", "Ноэлль", "Барбара",
    "Венти", "Эола", "Лиза ( ͡° ͜ʖ ͡°)",
    "Кокоми", "",
    "Фишль", "Гань Юй", "Паймон",
    "Путешественник", "СтасБарецкий228",
    "Ваша жаба", "Дед", "Буба",
    "Консерва", "мда", "кринж",
    "амогус", "сус", "сырник",
)


@bp.on.message(command="начать")
async def standard_wish(message: Message):
    async with aiosqlite.connect("db.db") as db:
        async with db.execute(
            "SELECT user_id FROM players WHERE user_id=(?)",
            (message.from_id,)
        ) as cursor:
            if await cursor.fetchone():
                await message.answer("Вы уже зашли в Genshin Impact")
            else:
                await db.execute(
                    "INSERT INTO players (user_id, nickname) VALUES (?, ?)",
                    (message.from_id, random.choice(NAMES),)
                )
                await db.commit()
                await message.answer("Вы зашли в Genshin Impact! Напишите !персонаж, что бы увидеть ваш никнейм и количество молитв")
