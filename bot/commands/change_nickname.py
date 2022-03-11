from vkbottle.bot import Blueprint, Message
import aiosqlite
import random

bp = Blueprint("Nickname changer")
bp.labeler.vbml_ignore_case = True

ONCHANGE_ANS = (
    "{}? Почему не Ху Тао",
    "{}? Опять нового перса спойлерят...",
    "Кринж",
    "{} норм перс кста"
)

YOUR_TOAD_ANS = (
    "{}? В следующий раз попроси кого-нибудь подумать за тебя",
    "{}? Не, ну просто шикарное имя!",
    "{}? Ну... Можно было придумать что-нибудь получше"
)

HU_TAO_ANS = "Самый лучший персонаж в игре (кто не согласен, тому бан)"

KEQING_ANS = "Один из лучших персонажей в игре (на втором месте)"

AMBER_ANS = "Лучший стрелок"


@bp.on.message(text=("!установить имя <nickname>", "!установить ник <nickname>", "!дать жабе имя <nickname>"))
async def give_nickname(message: Message, nickname):
    async with aiosqlite.connect("db.db") as db:
        async with db.execute("SELECT user_id FROM players WHERE user_id=(?)", (message.from_id,)) as cur:
            result = await cur.fetchone()
            if not result:
                await message.answer("Для начала нужно зайти в Genshin Impact командой !начать")
                return

        await db.execute("UPDATE players SET nickname=(?) WHERE user_id=(?)", (nickname, message.from_id))
        await db.commit()

    text = message.text.lower()
    nickname_low = nickname.lower()
    if text.startswith("!дать жабе имя "):
        reaction_answer = random.choice(YOUR_TOAD_ANS)
    else:
        if nickname_low in ("ху тао", "hu tao"):
            reaction_answer = HU_TAO_ANS
        elif nickname_low in ("эмбер", "amber"):
            reaction_answer = AMBER_ANS
        elif nickname_low in ("кэ цин", "keqing"):
            reaction_answer = KEQING_ANS
        else:
            reaction_answer = random.choice(ONCHANGE_ANS)
    await message.answer(reaction_answer.format(nickname)+"\n"+"Вы успешно поменяли никнейм")
