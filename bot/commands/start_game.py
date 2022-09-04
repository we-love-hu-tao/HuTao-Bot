from vkbottle.bot import Blueprint, Message
from loguru import logger
from utils import give_character
import create_pool
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
    "амогус", "сырник",
    "0); DROP DATABASE users; --",
    "Null Null", "c6 Ху Тао", "донатер",
    "Богдан",
    "В этом нике явно больше, чем 35 символов"
)


@bp.on.chat_message(text="!начать")
async def standard_wish(message: Message):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        is_exists = await pool.fetchrow(
            "SELECT user_id FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )
        if is_exists is not None:
            await message.answer("Вы уже зашли в Genshin Impact")
        else:
            new_nickname = random.choice(NAMES)
            logger.info(
                f"Пользователь {message.from_id} создал аккаунт в беседе {message.peer_id}, "
                f"случайный никнейм: {new_nickname}"
            )
            await pool.execute(
                "INSERT INTO players (user_id, peer_id, nickname) VALUES "
                "($1, $2, $3)",
                message.from_id, message.peer_id, new_nickname
            )
            await message.answer(
                "Вы зашли в Genshin Impact!\n"
                "Напишите !персонаж, что бы увидеть ваш никнейм "
                "и количество примогемов"
            )

            # Эмбер
            await give_character(
                message.from_id,
                message.peer_id,
                "rare_standard_characters",
                21
            )

            # Кэйа
            await give_character(
                message.from_id,
                message.peer_id,
                "rare_standard_characters",
                6
            )

            # Лиза
            await give_character(
                message.from_id,
                message.peer_id,
                "rare_standard_characters",
                7
            )

            # Барбара
            await give_character(
                message.from_id,
                message.peer_id,
                "rare_standard_characters",
                1
            )
