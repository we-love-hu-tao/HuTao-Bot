from typing import Optional

import create_pool
from config import ADMIN_IDS
from loguru import logger
from models.avatar import Avatar
from models.player_profile import PlayerInfo
from utils import (
    get_avatar_data,
    get_player_info,
    get_text_map,
    resolve_id,
    resolve_map_hash,
    translate
)
from variables import FAV_AVATARS
from vkbottle import Callback, GroupEventType, Keyboard
from vkbottle import KeyboardButtonColor as Color
from vkbottle import ShowSnackbarEvent
from vkbottle.bot import BotLabeler, Message, MessageEvent, rules
from vkbottle.http import AiohttpClient

bl = BotLabeler()
bl.vbml_ignore_case = True

http_client = AiohttpClient()


async def generate_avatars_kbd(from_id, uid, show_avatars):
    avatar_data = await get_avatar_data()
    text_map = await get_text_map()

    keyboard = Keyboard(inline=True)
    item_kbd = 0
    for avatar in show_avatars:
        avatar_show_info: Avatar = resolve_id(avatar.avatar_id, avatar_data)
        if avatar_show_info is None:
            continue

        item_kbd += 1
        if item_kbd > 1:
            keyboard.row()
            item_kbd = 0

        avatar_name_text = resolve_map_hash(text_map, avatar_show_info.name_text_map_hash)
        color = Color.SECONDARY
        if avatar.level >= 90:
            color = Color.PRIMARY
        else:
            avatar_name_text += f" (Ур. {avatar.level})"

        if avatar.avatar_id == 10000046:
            color = Color.POSITIVE

        avatar_kbd_text = Callback(
            avatar_name_text,
            payload={
                "caller_id": from_id,
                "uid": uid,
                "avatar_id": avatar.avatar_id,
                "avatar_name": avatar_name_text,
            },
        )

        keyboard.add(avatar_kbd_text, color)
    return keyboard.get_json()


@bl.message(
    text=("!геншин инфо", "!геншин инфо <uid:int>", "! геншин инфо", " ! геншин инфо <uid:int>")
)
async def genshin_info(message: Message, uid: Optional[int] = None):
    info_msg = ""

    if uid is None:
        pool = create_pool.pool
        async with pool.acquire() as pool:
            if message.reply_message is None:
                uid_request = await pool.fetchrow(
                    "SELECT uid FROM players WHERE user_id=$1 AND peer_id=$2",
                    message.from_id,
                    message.peer_id,
                )

                if uid_request is None or uid_request["uid"] is None:
                    return await translate("genshin_info", "uid_not_set")
            else:
                uid_request = await pool.fetchrow(
                    "SELECT uid FROM players WHERE user_id=$1 AND peer_id=$2",
                    message.reply_message.from_id,
                    message.peer_id,
                )

                if uid_request is None or uid_request["uid"] is None:
                    return await translate("genshin_info", "replier_no_uid")

                info_msg += (
                    (await translate("genshin_info", "player_info"))
                    .format(from_id=message.reply_message.from_id)
                    + "\n\n"
                )

            uid = uid_request["uid"]

    try:
        player_info = (await get_player_info(http_client, uid, only_info=True)).player_info
    except Exception as e:
        logger.error(e)
        return (
            await translate("genshin_info", "enka_network_error")
        ).format(user_id=ADMIN_IDS[0]) + "\n" + str(e)

    if not player_info:
        if uid is None:
            return await translate("genshin_info", "current_account_deleted")
        else:
            return await translate("genshin_info", "uid_not_found")

    player_info: PlayerInfo

    unknown = await translate("genshin_info", "unknown_value")
    nickname = player_info.nickname or unknown
    adv_rank = player_info.level or unknown
    signature = player_info.signature or unknown
    world_level = player_info.world_level or unknown
    show_avatars = player_info.show_avatar_info_list or None

    profile_picture_id: int | None = (
        player_info.profile_picture.avatar_id or player_info.profile_picture.id or None
    )
    avatar_picture_name = unknown
    if profile_picture_id:
        if profile_picture_id < 10000000:
            # handling enka.network's different avatar ids
            profile_picture_id += 9900000

        avatar_data = await get_avatar_data()
        text_map = await get_text_map()
        avatar_picture_info: Avatar = resolve_id(profile_picture_id, avatar_data)
        if avatar_picture_info:
            avatar_picture_name = resolve_map_hash(text_map, avatar_picture_info.name_text_map_hash)

    keyboard = None
    if show_avatars is not None and len(show_avatars) > 0:
        keyboard = await generate_avatars_kbd(message.from_id, uid, show_avatars)

    info_msg += (
        await translate('genshin_info', 'info_msg_start')
    ).format(uid=uid, nickname=nickname) + '\n'

    if profile_picture_id in FAV_AVATARS:
        info_msg += (
            await translate("genshin_info", "fav_avatar_profile_picture")
        ).format(avatar_name=avatar_picture_name)
    elif avatar_picture_name is None:
        info_msg += (await translate("genshin_info", "no_avatar_profile_picture"))
    else:
        info_msg += (
            await translate("genshin_info", "avatar_profile_picture")
        ).format(avatar_name=avatar_picture_name)
    info_msg += '\n\n'

    info_msg += (
        f"{await translate('genshin_info', 'adv_rank')}: {adv_rank}\n"
        f"{await translate('genshin_info', 'description')}: {signature}\n"
        f"{await translate('genshin_info', 'world_level')}: {world_level}\n\n"
        f"{await translate('genshin_info', 'more_information')}: https://enka.network/u/{uid}"
    )

    await message.answer(info_msg, keyboard=keyboard, disable_mentions=True)


# https://api.enka.network/#/api?id=fightprop
FIGHT_PROP_NAMES = {
    '2000': 1377450402,  # HP
    '2001': 1756301290,  # ATK
    '2002': 3591287138,  # DEF
    '28': 3421163681,    # Elemental Mastery
    '20': 1916797986,    # CRIT Rate
    '22': 4137936461,    # CRIT DMG
    '26': 3911103831,    # Heal Bonus
    '23': 1735465728,    # Energy Recharge
    '30': 3763864883,    # Physical DMG Bonus
    '40': 999734248,     # Pyro DMG Bonus
    '41': 3514877774,    # Electro DMG Bonus
    '42': 3619239513,    # Hydro DMG Bonus
    '43': 1824382851,    # Dendro DMG Bonus
    '44': 312842903,     # Anemo DMG Bonus
    '45': 2557985416,    # Geo DMG Bonus
    '46': 4054347456,    # Cryo DMG Bonus
}
FIGHT_PROP_EMOJIS = {
    '2000': '💖',
    '2001': '⚔️',
    '2002': '🛡️',
    '20': '💥',
    '22': '🗡️',
    '23': '⚡',
    '26': '💊',
    '28': '🌀',
    '30': '🔥',
    '40': '🔥',
    '41': '⚡',
    '42': '💧',
    '43': '🌳',
    '44': '💨',
    '45': '🪨',
    '46': '❄️',
}
FIGHT_PROP_DECIMAL = (
    '20', '22', '23', '26', '30', '40', '41', '42', '43', '44', '45', '46'
)


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadMapRule([
        ("caller_id", int), ("uid", int), ("avatar_id", int), ("avatar_name", str)
    ]),
)
async def show_avatar_info(event: MessageEvent):
    payload = event.get_payload_json()
    if payload is None:
        logger.error("Couldn't get event payload")
        return

    caller_id = payload['caller_id']
    if caller_id != event.object.user_id:
        await event.ctx_api.messages.send_message_event_answer(
            event_id=event.object.event_id,
            user_id=event.object.user_id,
            peer_id=event.object.peer_id,
            event_data=ShowSnackbarEvent(
                text=await translate("genshin_info", "only_caller_build")
            ).json(),
        )
        return

    uid = payload['uid']
    avatar_id = payload['avatar_id']
    avatar_name = payload['avatar_name']
    try:
        player_info = await get_player_info(http_client, uid)
    except Exception as e:
        logger.error(e)
        await event.edit_message(await translate("genshin_info", "get_build_error"))
        return

    msg = (
        await translate("genshin_info", "avatar_info_start")
    ).format(avatar_name=avatar_name, uid=uid)
    msg += '\n'
    avatars_info = player_info.avatar_info_list
    if avatars_info is None:
        await event.edit_message(await translate("genshin_info", "detailed_info_disabled"))
        return
    avatar = None
    for avatar in avatars_info:
        if avatar.avatar_id == avatar_id:
            break
    if avatar is None:
        await event.edit_message(await translate("genshin_info", "avatar_removed_from_stand"))
        return
    fight_prop_map = avatar.fight_prop_map
    fight_prop_map = {k: v for k, v in fight_prop_map.items() if v > 0}

    text_map = await get_text_map()
    for k, v in FIGHT_PROP_NAMES.items():
        if k not in fight_prop_map:
            continue

        fight_prop_val = fight_prop_map.get(k)
        if fight_prop_val is None:
            logger.warning(f"Unknown fight prop value: {k}")
            continue
        if k in FIGHT_PROP_DECIMAL:
            fight_prop_val = round(fight_prop_val * 100, 1)
        else:
            fight_prop_val = round(fight_prop_val)

        emoji = ''
        if k in FIGHT_PROP_EMOJIS:
            emoji = FIGHT_PROP_EMOJIS[k] + ' | '

        msg += f"{emoji}{resolve_map_hash(text_map, v)}: {fight_prop_val}\n"

    # We use `copy()` since `get_player_info()` is cached, if we change
    # `show_avatar_info_list` without using `copy()`, then
    # `player_info.player_info.show_avatar_info_list` will also change
    # and will be returned every time we call `get_player_info()`
    show_avatar_info_list = player_info.player_info.show_avatar_info_list.copy()
    logger.info(show_avatar_info_list)
    for avatar in show_avatar_info_list:
        if avatar.avatar_id == avatar_id:
            show_avatar_info_list.remove(avatar)
            break

    keyboard = await generate_avatars_kbd(
        caller_id, uid, show_avatar_info_list
    )
    await event.edit_message(msg, keyboard=keyboard)
