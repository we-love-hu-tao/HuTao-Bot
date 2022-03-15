from vkbottle.bot import Blueprint, Message
from vkbottle.user import User
from vkbottle import VKAPIError
from player_exists import HasAccount
import aiosqlite
import random

bp = Blueprint("Nickname changer")
bp.labeler.vbml_ignore_case = True

# Только попробуй с этим что-то сделать
user_token = "e3937298e8c98ef244c6fd059df249dbe8d2aa45bf48079e2cbc538c77cd22c4d8d7e5fa332d3571185ff"  # noqa: E501
user = User(user_token)

ONCHANGE_ANS = (
    "{}? Почему не Ху Тао",
    "{}? Опять нового перса спойлерят...",
    "Кринж",
    "{} норм перс кста"
)

BETTER_NOT_USE = (
    "ху тао хуйня", "ху тао говно",
    "ху тао шлюха", "ху тао тупая",
    "хуйтао", "hu tao sucks",
    "ху тао кринж"
    "кэ цин хуйня", "кэ цин говно",
    "кэ цин шлюха", "кэ цин тупая",
    "кэ цин кринж"
    "кека хуйня", "кека говно",
    "кека шлюха", "кека тупая",
    "кека кринж"
    "хуйцин", "keqing sucks",
    "эмбер хуйня", "эмбер говно",
    "эмбер шлюха", "эмбер тупая",
    "хуйэмбер", "amber sucks",
    "эмбер кринж",
)

BETTER_NOT_USE_ANS = (
    "Ты ишак", "Всем всё равно",
    "Завтра тебя забанят не только тут",
    "Не стоило этого делать",
    "Сделай домашние задания, тебе завтра в школу",
    "В эту ночь тебе лучше не спать",
)

YOUR_TOAD_ANS = (
    "{}? В следующий раз попроси кого-нибудь подумать за тебя",
    "{}? Не, ну просто шикарное имя!",
    "{}? Ну... Можно было придумать что-нибудь получше"
)

HU_TAO_ANS = "Самый лучший персонаж в игре (кто не согласен, тому бан)"

KEQING_ANS = "Один из лучших персонажей в игре (на втором месте)"

AMBER_ANS = "Лучший стрелок"


@bp.on.message(HasAccount(), text=("!установить имя <nickname>", "!установить ник <nickname>", "!дать жабе имя <nickname>"))
async def give_nickname(message: Message, nickname):
    bad = False
    text = message.text.lower()
    nickname_low = nickname.lower()

    if not any(bad_item in nickname_low for bad_item in BETTER_NOT_USE):
        async with aiosqlite.connect("db.db") as db:
            await db.execute("UPDATE players SET nickname=(?) WHERE user_id=(?)", (nickname, message.from_id))
            await db.commit()
    else:
        bad = True

    if text.startswith("!дать жабе имя "):
        reaction_answer = random.choice(YOUR_TOAD_ANS)
    else:
        if nickname_low in ("ху тао", "hu tao"):
            reaction_answer = HU_TAO_ANS
        elif nickname_low in ("эмбер", "amber"):
            reaction_answer = AMBER_ANS
        elif nickname_low in ("кэ цин", "keqing"):
            reaction_answer = KEQING_ANS
        elif bad:
            await message.answer(
                "Вы были забанены в группе.\n"
                "Для разбана, напишите извинение (минимум 200 слов) "
                "и отправьте его [id322615766|мне] в личные сообщения\n"
                f'"{random.choice(BETTER_NOT_USE_ANS)}"'
            )
            await user.api.groups.ban(
                group_id=193964161,
                owner_id=message.from_id,
                comment="Оскорбление важного персонажа",
                comment_visible=1
            )

            try:
                a = await bp.api.messages.remove_chat_user(
                    chat_id=message.chat_id,
                    user_id=message.from_id
                )
                print(a)
            except VKAPIError as e:
                print(e)

            return
        else:
            reaction_answer = random.choice(ONCHANGE_ANS)
    await message.answer(reaction_answer.format(nickname)+"\n"+"Вы успешно поменяли никнейм")
