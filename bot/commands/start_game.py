import random

import msgspec
from loguru import logger
from vkbottle import Keyboard, Text
from vkbottle.bot import Blueprint, Message

import create_pool
from item_names import PRIMOGEM
from utils import give_avatar, give_item

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
    "Чокола", "Ванилла",
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
PROFILE_INFO_KEYBOARD = (
    Keyboard(inline=True)
    .add(Text("Персонаж"))
)


@bp.on.chat_message(text="!начать")
async def start_game(message: Message):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        is_exists = await pool.fetchrow(
            "SELECT user_id FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )
        if is_exists is not None:
            return "В этом чате вы уже присоединились к боту"
        else:
            new_nickname = random.choice(NAMES)
            logger.info(
                f"User {message.from_id} has created an account in a chat {message.peer_id}, "
                f"random nickname: {new_nickname}"
            )
            await pool.execute(
                "INSERT INTO players (user_id, peer_id, nickname) VALUES "
                "($1, $2, $3)",
                message.from_id, message.peer_id, new_nickname
            )

            # Giving 6400 primogems and avatars to the player
            await give_item(message.from_id, message.peer_id, PRIMOGEM, 6400)
            avatars = await pool.fetchrow(
                "SELECT avatars FROM players WHERE user_id=$1 AND peer_id=$2 ",
                message.from_id, message.peer_id
            )
            avatars = msgspec.json.decode(avatars['avatars'].encode("utf-8"))
            avatars = give_avatar(avatars, 1021)  # Amber
            avatars = give_avatar(avatars, 1015)  # Kaeya
            avatars = give_avatar(avatars, 1006)  # Lisa
            avatars = give_avatar(avatars, 1014)  # Barbara
            await pool.execute(
                "UPDATE players SET avatars=$1 ::jsonb WHERE user_id=$2 AND peer_id=$3",
                msgspec.json.encode(avatars).decode("utf-8"), message.from_id, message.peer_id
            )

            await message.answer(
                "Вы присоединились к боту!\n"
                "Напишите !персонаж, что бы увидеть ваш никнейм "
                "и количество примогемов",
                keyboard=PROFILE_INFO_KEYBOARD
            )
