import time

import msgspec
from vkbottle import Keyboard
from vkbottle import KeyboardButtonColor as Color
from vkbottle import Text
from vkbottle.bot import BotLabeler, Message
from vkbottle.http import AiohttpClient

import create_pool
from item_names import ACQUAINT_FATE, ADVENTURE_EXP, INTERTWINED_FATE, PRIMOGEM
from utils import count_quests_time, exists, exp_to_level, get_item, ACHIEVEMENTS

bl = BotLabeler()
bl.vbml_ignore_case = True

http_client = AiohttpClient()


@bl.message(text=(
    '!персонаж', '!перс', '!gthc', '! перс',
    '[<!>|<!>] Персонаж', 'Персонаж',
))
async def profile(message: Message):
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        result = await pool.fetchrow(
            "SELECT "
            "nickname, "
            "uid, "
            "gacha_info, "
            "reward_last_time, "
            "daily_quests_time, "
            "doing_quest "
            "FROM players WHERE user_id=$1 and peer_id=$2",
            message.from_id, message.peer_id
        )

    nickname = result['nickname']
    UID = result['uid']

    gacha_info = msgspec.json.decode(result['gacha_info'].encode("utf-8"))
    if len(gacha_info) > 0:
        event_pity5 = gacha_info['eventCharacterBanner']['pity5']
    else:
        event_pity5 = 0

    reward_last_time = result['reward_last_time']
    started_time = result['daily_quests_time']
    doing_quest = result['doing_quest']

    experience = await get_item(ADVENTURE_EXP, message.from_id, message.peer_id)
    experience = experience['count']
    level = exp_to_level(experience)
    quest_time = count_quests_time(experience)

    primogems = await get_item(PRIMOGEM, message.from_id, message.peer_id)
    primogems = primogems['count']

    standard_wishes = await get_item(ACQUAINT_FATE, message.from_id, message.peer_id)
    standard_wishes = standard_wishes['count']

    event_wishes = await get_item(INTERTWINED_FATE, message.from_id, message.peer_id)
    event_wishes = event_wishes['count']

    keyboard = Keyboard(inline=True)
    if int(time.time()) > reward_last_time + 86400:
        keyboard.add(Text("Награда"), color=Color.POSITIVE)

    if started_time + 86400 < int(time.time()) and doing_quest is False:
        keyboard.add(Text("Начать поручения"))

    if started_time + quest_time < int(time.time()) and doing_quest:
        keyboard.add(Text("Завершить поручения"), color=Color.POSITIVE)

    await message.answer(
        f"&#128100; | Ник: {nickname}\n"
        f"&#128200; | Уровень: {level}\n"
        f"&#128160; | Примогемы: {primogems}\n"
        f"&#128311; | Стандартных молитв: {standard_wishes}\n"
        f"&#128310; | Молитв события: {event_wishes}\n\n"

        f"&#10133; | Гарант в ивентовых баннерах: {event_pity5}\n\n"

        f"&#128100; | Айди в Genshin Impact: {UID if UID else 'не установлен!'}",
        keyboard=keyboard.get_json()
    )


@bl.message(text=(
    '!баланс', '!крутки', '!примогемы', '! баланс'
))
async def check_balance(message: Message):
    if not await exists(message):
        return

    primogems = await get_item(PRIMOGEM, message.from_id, message.peer_id)
    primogems = primogems['count']

    event_wishes = await get_item(INTERTWINED_FATE, message.from_id, message.peer_id)
    event_wishes = event_wishes['count']
    standard_wishes = await get_item(ACQUAINT_FATE, message.from_id, message.peer_id)
    standard_wishes = standard_wishes['count']

    return (
        f"&#128160; | Примогемы: {primogems}\n"
        f"&#128160; | Ивентовые крутки: {event_wishes}\n"
        f"&#128160; | Стандартные крутки: {standard_wishes}"
    )


@bl.message(text=("!достижения", "!ачивки"))
async def view_achievements(message: Message):
    msg = None
    for num, i in enumerate(ACHIEVEMENTS, 1):
        msg += str(num)+'. '+ACHIEVEMENTS[i]['name']
        if ACHIEVEMENTS[i]['progress'] is True:
            pass

        msg += '\n'+ACHIEVEMENTS[i]['description']

    return msg

