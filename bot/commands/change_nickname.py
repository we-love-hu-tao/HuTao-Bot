from vkbottle.bot import Blueprint, Message
from vkbottle.user import User
from vkbottle import VKAPIError
from player_exists import exists
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
    "{} норм перс кста",
)

# мне было плохо, пока я это писал
BETTER_NOT_USE = (
    "ху тао хуйня",
    "ху тао хуета",
    "ху тао говно",
    "ху тао шлюха",
    "ху тао тупая",
    "ху тао кринж",
    "ху тао плохая",
    "ху тао днище",
    "хуйтао",
    "hu tao sucks",
    "кэ цин хуйня",
    "кэ цин хуета",
    "кэ цин говно",
    "кэ цин шлюха",
    "кэ цин тупая",
    "кэ цин кринж",
    "кэ цин плохая"
    "кэ цин днище",
    "кека хуйня",
    "кека хуета",
    "кека говно",
    "кека шлюха",
    "кека тупая",
    "кека кринж",
    "кека плохая"
    "кека днище",
    "хуйцин",
    "keqing sucks",
    "эмбер хуйня",
    "эмбер хуета",
    "эмбер говно",
    "эмбер шлюха",
    "эмбер тупая",
    "эмбер кринж",
    "эмбер плохая"
    "эмбер днище",
    "хуйэмбер",
    "amber sucks",
)

BETTER_NOT_USE_ANS = (
    "Ты ишак",
    "Всем всё равно",
    "Завтра тебя забанят не только тут",
    "Не стоило этого делать",
    "Сделай домашние задания, тебе завтра в школу",
    "В эту ночь тебе лучше не спать",
)

YOUR_TOAD_ANS = (
    "{}? В следующий раз попроси кого-нибудь подумать за тебя",
    "{}? Не, ну просто шикарное имя!",
    "{}? Ну... Можно было придумать что-нибудь получше",
)

HU_TAO_ANS = "Самый лучший персонаж в игре (кто не согласен, тому бан)"

KEQING_ANS = "Её реран будет."

AMBER_ANS = "Лучший стрелок"


@bp.on.message(
    text=(
        "!установить имя <nickname>",
        "!установить ник <nickname>",
        "!дать жабе имя <nickname>",
    )
)
async def give_nickname(message: Message, nickname):
    if not await exists(message):
        return
    bad = False
    text = message.text.lower()
    nickname_low = nickname.lower()

    if not any(bad_item in nickname_low for bad_item in BETTER_NOT_USE):
        async with aiosqlite.connect("db.db") as db:
            await db.execute(
                "UPDATE players SET nickname=(?) WHERE user_id=(?)",
                (nickname, message.from_id),
            )
            await db.commit()
    else:
        bad = True

    if text.startswith("!дать жабе имя "):
        reaction_answer = random.choice(YOUR_TOAD_ANS)
    else:
        if bad:
            async with aiosqlite.connect("db.db") as db:
                await db.execute(
                    "UPDATE players SET banned=1 WHERE user_id=(?)",
                    (message.from_id,),
                )
                await db.commit()
            await user.api.groups.ban(
                group_id=193964161,
                owner_id=message.from_id,
                comment="Оскорбление важного персонажа",
                comment_visible=1,
            )
            await message.answer(
                "Вы были забанены в группе.\n"
                "Для разбана, напишите извинение (минимум 200 слов) "
                "и отправьте его [id322615766|мне] в личные сообщения\n"
                f'"{random.choice(BETTER_NOT_USE_ANS)}"'
            )

            try:
                a = await bp.api.messages.remove_chat_user(
                    chat_id=message.chat_id, user_id=message.from_id
                )
                print(a)
            except VKAPIError as e:
                print(e)

            return
        elif nickname_low in ("ху тао", "hu tao"):
            reaction_answer = HU_TAO_ANS
        elif nickname_low in ("эмбер", "amber"):
            reaction_answer = AMBER_ANS
        elif nickname_low in ("кэ цин", "keqing"):
            reaction_answer = KEQING_ANS
        else:
            reaction_answer = random.choice(ONCHANGE_ANS)
    await message.answer(
        reaction_answer.format(nickname) + "\n" + "Вы успешно поменяли никнейм"
    )
