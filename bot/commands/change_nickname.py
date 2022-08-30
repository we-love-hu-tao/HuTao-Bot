from vkbottle.bot import Blueprint, Message
from vkbottle.user import User
from vkbottle import VKAPIError
from loguru import logger
from variables import GROUP_ID, VK_USER_TOKEN
from player_exists import exists
import random
import create_pool

bp = Blueprint("Nickname changer")
bp.labeler.vbml_ignore_case = True

user = User(VK_USER_TOKEN)

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
    "Когда кто-то спрашивает, в чем смысл жизни, сразу можно понять, "
    "что этот человек еще не видел её",
    "Геншин был бы худшей гачи игрой в мире, если бы в ней не было её",
    "Настоящий пиро архонт"
)

TIMUR_ANS = (
    "&#129320;",
    "Как же я хочу заснуть, а проснуться в Тейвате, рядом с ритуальным бюро Ваншэн..."
)

KEQING_ANS = (
    "Настоящий электро архонт",
    "Ножки &#128563;&#128563;",
    "Её реран будет."
)

AMBER_ANS = (
    "Возможно я стану чаще играть в геншин, если хойоверсв её баффнут",
    "Её мейнеры прекрасные люди",
    "На одном уровне с Ёимией"
)

YOIMIYA_ANS = (
    "МА-ТЕ-РИ-А-ЛЫ!",
    "4 стрелы - все в голубя"
)

KOKOMI_ANS = (
    "Настоящий гидро архонт (лучше Барбары)",
    "+100 энергии"
)

AYAKA_ANS = (
    "Её мейнеры самые токсичные люди на планете",
    "Аятао канон?????"
)

QIQI_ANS = (
    "&#128128;",
    "&#9760;"
)


async def change_nickname(user_id: int, peer_id: int, nickname: str, pool):
    logger.info(
        f'Устанавливание никнейма "{nickname}" пользователю {user_id} в беседе {peer_id}'
    )
    await pool.execute(
        "UPDATE players SET nickname=$1 WHERE user_id=$2 AND peer_id=$3",
        nickname, user_id, peer_id,
    )


async def check_for_swear(nickname: str):
    logger.debug("checking for swears")
    for swear in CUSTOM_SWEARS:
        if swear in nickname:
            logger.info(f'В никнейме "{nickname}" нашлось особое оскорбление: {swear}')
            return True

    for character in PROTECTED_CHAR:
        for swear in POSSIBLE_SWEARS:
            if f"{character} {swear}" in nickname:
                logger.info(f'В никнейме "{nickname}" нашлось обычное оскорбление: {swear}')
                return True
    logger.info(f'В никнейме "{nickname}" не нашлось оскорблений')
    return False


@bp.on.chat_message(
    text=(
        "!установить имя <nickname>",
        "!установить ник <nickname>",
        "!ник <nickname>",
        "!дать жабе имя <nickname>",
    )
)
async def give_nickname(message: Message, nickname):
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:

        text = message.text.lower()
        nickname_low = nickname.lower()

        has_swear = await check_for_swear(nickname)
        if not has_swear:
            if len(nickname) < 35:
                await change_nickname(message.from_id, message.peer_id, nickname, pool)
            else:
                await message.answer("В нике не может быть больше 35 символов (включая пробел)")
                return
        else:
            logger.info(f'Бан пользователя {message.from_id} за оскорбление персонажа (БД)')
            await pool.execute(
                "INSERT INTO banned (user_id) VALUES ($1)",
                message.from_id
            )
            logger.info(f'Бан пользователя {message.from_id} за оскорбление персонажа (группа)')
            await user.api.groups.ban(
                group_id=GROUP_ID,
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
                logger.info(
                    f'Попытка забанить пользователя {message.from_id} в беседе {message.peer_id}'
                )
                await bp.api.messages.remove_chat_user(
                    chat_id=message.chat_id, user_id=message.from_id
                )
            except VKAPIError as error:
                logger.info(
                    f'К сожалению, забанить пользователя {message.from_id} '
                    f'в беседе {message.peer_id} не получилось, ошибка: {error}'
                )
                return (
                    "А, еще, просьба к администратору беседы - выдайте мне пожалуйста "
                    "админку, что бы я мог нормально работать (точно никак не связано "
                    "с предыдущими событиями)"
                )

            return

        if text.startswith("!дать жабе имя "):
            reaction_answer = random.choice(YOUR_TOAD_ANS)
        else:
            if nickname_low in ("ху тао", "хутава", "hu tao", "hutao"):
                reaction_answer = random.choice(HU_TAO_ANS)
            elif nickname_low in ("тимур", "богданов"):
                reaction_answer = random.choice(TIMUR_ANS)
            elif nickname_low in ("эмбер", "amber"):
                reaction_answer = random.choice(AMBER_ANS)
            elif nickname_low in ("кэ цин", "кека", "keqing"):
                reaction_answer = random.choice(KEQING_ANS)
            elif nickname_low in ("ёимия", "еимия", "yoimiya"):
                reaction_answer = random.choice(YOIMIYA_ANS)
            elif nickname_low in ("кокоми", "kokomi"):
                reaction_answer = random.choice(KOKOMI_ANS)
            elif nickname_low in ("аяка", "ayaka"):
                reaction_answer = random.choice(AYAKA_ANS)
            elif nickname_low in ("ци-ци", "ци ци", "цици", "чича", "qiqi"):
                reaction_answer = random.choice(QIQI_ANS)
            else:
                reaction_answer = random.choice(ONCHANGE_ANS)
        return reaction_answer.format(nickname) + "\n" + "Вы успешно поменяли никнейм"
