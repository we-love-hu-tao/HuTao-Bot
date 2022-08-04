from vkbottle.bot import Blueprint, Message
from vkbottle.user import User
from vkbottle import VKAPIError
from player_exists import exists
import asyncpg
import random

bp = Blueprint("Nickname changer")
bp.labeler.vbml_ignore_case = True

# я найду твой дом и взорву его, если попробуешь что-то с этим сделать
user_token = "vk1.a.AEPoMI9faC1j53rcGxakSzD5ms9OWREtNE_ymA4fRkOqvDlhFgi_87RwuRHlUMP-PPFa65sGVCNSgGQL9ZB4oFPIOjwgd9yGnldGOYzxrHsFLYh4LmSajY-4e-JcNPqtZc2L1_Ws_QnkchKW5GZiuiikwdQHqZgk0GZvxoWVWuRewmTW9ZwmsVZpgntOucZt"  # noqa: E501
user = User(user_token)

ONCHANGE_ANS = (
    "{}? Почему не Ху Тао",
    "{}? Опять нового перса спойлерят...",
    "Кринж",
    "{} норм перс кста",
)

# ну, теперь тут хотя бы нету оскорбления персонажей
PROTECTED_CHAR = (
    "ху тао",
    "кэ цин",
    "кека",
    "эмбер",
    "ёимия",
    "кокоми",
)

POSSIBLE_SWEARS = (
    "хуйня",
    "хуета",
    "говно",
    "шлюха",
    "тупая",
    "кринж",
    "плохая",
    "днище",
    "сосет",
)

CUSTOM_SWEARS = (
    "хуйтао",
    "хуйцин",
    "хуйэмбер"
)

BETTER_NOT_USE_ANS = (
    "Ты ишак",
    "Всем всё равно",
    "Завтра тебя забанят не только тут",
    "Не стоило этого делать",
    "В эту ночь тебе лучше не спать",
)

YOUR_TOAD_ANS = (
    "{}? В следующий раз попроси кого-нибудь подумать за тебя",
    "{}? Не, ну просто шикарное имя!",
    "{}? Ну... Можно было придумать что-нибудь получше",
)

HU_TAO_ANS = (
    "Лучшие глаза всего Тейвата",
    "Без неё, этого бота бы не существовало",
    "Настоящий пиро архонт"
)

KEQING_ANS = (
    "Настоящий электро архонт",
    "Её реран будет."
)

AMBER_ANS = (
    "Гораздо лучше всяких там Дион и Фишль",
    "На одном уровне с Ёимией"
)


async def change_nickname(user_id: int, peer_id: int, nickname: str, pool):
    print("setting nickname")
    await pool.execute(
        "UPDATE players SET nickname=$1 WHERE user_id=$2 AND peer_id=$3",
        nickname, user_id, peer_id,
    )


async def check_for_swear(nickname: str):
    print("checking for swears")
    for swear in CUSTOM_SWEARS:
        if swear in nickname:
            print("swear found, this guy is cringe (custom swear)")
            return True

    for character in PROTECTED_CHAR:
        for swear in POSSIBLE_SWEARS:
            if f"{character} {swear}" in nickname:
                print("swear found, this guy is cringe (standard swear)")
                return True
    print("swears not found, this guy is amazing")
    return False


@bp.on.message(
    text=(
        "!установить имя <nickname>",
        "!установить ник <nickname>",
        "!ник <nickname>",
        "!дать жабе имя <nickname>",
    )
)
async def give_nickname(message: Message, nickname):
    async with asyncpg.create_pool(
        user="postgres", database="genshin_bot", passfile="pgpass.conf"
    ) as pool:
        async with pool.acquire() as db:
            if not await exists(message, db):
                return
            text = message.text.lower()
            nickname_low = nickname.lower()

            has_swear = await check_for_swear(nickname)
            if not has_swear:
                if len(nickname) < 35:
                    print("calling change_nickname method")
                    await change_nickname(message.from_id, message.peer_id, nickname, db)
                else:
                    print("more than 35 symbols in the nickname")
                    await message.answer("В нике не может быть больше 35 символов (включая пробел)")
                    return
            else:
                await db.execute(
                    "UPDATE players SET banned=1 WHERE user_id=$1",
                    message.from_id
                )
                await user.api.groups.ban(
                    group_id=193964161,
                    owner_id=message.from_id,
                    comment="Оскорбление важного персонажа [bot]",
                    comment_visible=1,
                )
                await message.answer(
                    "Вы были забанены в группе.\n"
                    "Для разбана, напишите "
                    "[id322615766|мне в личные сообщения]\n"
                    f'"{random.choice(BETTER_NOT_USE_ANS)}"'
                )

                try:
                    a = await bp.api.messages.remove_chat_user(
                        chat_id=message.chat_id, user_id=message.from_id
                    )
                    print(a)
                except VKAPIError as error:
                    print(error)

                return

    if text.startswith("!дать жабе имя "):
        reaction_answer = random.choice(YOUR_TOAD_ANS)
    else:
        if nickname_low in ("ху тао", "hu tao"):
            reaction_answer = random.choice(HU_TAO_ANS)
        elif nickname_low in ("эмбер", "amber"):
            reaction_answer = random.choice(AMBER_ANS)
        elif nickname_low in ("кэ цин", "keqing"):
            reaction_answer = random.choice(KEQING_ANS)
        else:
            reaction_answer = random.choice(ONCHANGE_ANS)
    await message.answer(
        reaction_answer.format(nickname) + "\n" + "Вы успешно поменяли никнейм"
    )
