from typing import Optional

from enka.gi import Player, ShowcaseCharacter, ShowcaseResponse
from loguru import logger
from vkbottle import Callback, GroupEventType, Keyboard
from vkbottle import KeyboardButtonColor as Color
from vkbottle import ShowSnackbarEvent
from vkbottle.bot import BotLabeler, Message, MessageEvent, rules

import create_pool
from config import ADMIN_IDS
from models.avatar import Avatar
from utils import (
    get_avatar_data,
    get_player_info,
    get_text_map,
    resolve_id,
    resolve_map_hash,
    translate
)
from variables import FAV_AVATARS

bl = BotLabeler()
bl.vbml_ignore_case = True


async def generate_avatars_kbd(from_id, uid, showcase_avatars: list[ShowcaseCharacter]):
    avatar_data = await get_avatar_data()
    text_map = await get_text_map()

    keyboard = Keyboard(inline=True)
    item_kbd = 0
    for avatar in showcase_avatars:
        avatar_show_info: Avatar = resolve_id(avatar.id, avatar_data)
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

        if avatar.id == 10000046:
            color = Color.POSITIVE

        avatar_kbd_text = Callback(
            avatar_name_text,
            payload={
                "caller_id": from_id,
                "uid": uid,
                "avatar_id": avatar.id,
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
        player_info: Player = (await get_player_info(uid, info_only=True)).player
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

    unknown = await translate("genshin_info", "unknown_value")
    nickname = player_info.nickname or unknown
    adv_rank = player_info.level or unknown
    signature = player_info.signature or unknown
    world_level = player_info.world_level or unknown
    showcase_avatars = player_info.showcase_characters or None

    profile_picture_id: int = player_info.profile_picture_id
    avatar_picture_name = unknown

    avatar_data = await get_avatar_data()
    text_map = await get_text_map()
    avatar_picture_info: Avatar = resolve_id(profile_picture_id, avatar_data)
    if avatar_picture_info:
        avatar_picture_name = resolve_map_hash(text_map, avatar_picture_info.name_text_map_hash)

    keyboard = None
    if showcase_avatars:
        keyboard = await generate_avatars_kbd(message.from_id, uid, showcase_avatars)

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
STATS_TO_SHOW: tuple = (
    '2000',  # HP
    '2001',  # ATK
    '2002',  # DEF
    '28',    # Elemental Mastery
    '20',    # CRIT Rate
    '22',    # CRIT DMG
    '26',    # Heal Bonus
    '23',    # Energy Recharge
    '30',    # Physical DMG Bonus
    '40',    # Pyro DMG Bonus
    '41',    # Electro DMG Bonus
    '42',    # Hydro DMG Bonus
    '43',    # Dendro DMG Bonus
    '44',    # Anemo DMG Bonus
    '45',    # Geo DMG Bonus
    '46',    # Cryo DMG Bonus
)
STATS_EMOJIS = {
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
        player_info: ShowcaseResponse = await get_player_info(uid)
    except Exception as e:
        logger.error(e)
        await event.edit_message(await translate("genshin_info", "get_build_error"))
        return

    showcase_avatars = player_info.characters
    if not showcase_avatars:
        await event.edit_message(await translate("genshin_info", "detailed_info_disabled"))
        return
    avatar = None
    for avatar in showcase_avatars:
        if avatar.id == avatar_id:
            break
    if avatar is None:
        await event.edit_message(await translate("genshin_info", "avatar_removed_from_stand"))
        return

    msg = (
        await translate("genshin_info", "avatar_info_start")
    ).format(avatar_name=avatar_name, uid=uid)
    msg += '\n'

    avatar_stats = avatar.stats

    for stat in avatar_stats:
        stat_id = str(avatar_stats[stat].type.value)
        if stat_id not in STATS_TO_SHOW:
            # Skipping stats we don't know or aren't important
            continue
        if avatar_stats[stat].value == 0:
            # Skipping stats with no value
            continue

        stat_name = avatar_stats[stat].name
        stat_formatted_value = avatar_stats[stat].formatted_value
        emoji = '?'
        if stat_id in STATS_EMOJIS:
            emoji = STATS_EMOJIS[stat_id]

        msg += f"{emoji} | {stat_name}: {stat_formatted_value}\n"
    """
    fight_prop_map = {prop_id: v for prop_id, v in fight_prop_map.items() if v > 0}

    text_map = await get_text_map()
    for prop_id, v in FIGHT_PROP_NAMES.items():
        if prop_id not in fight_prop_map:
            continue

        fight_prop_val = fight_prop_map.get(prop_id)
        if fight_prop_val is None:
            logger.warning(f"Unknown fight prop value: {prop_id}")
            continue
        if prop_id in FIGHT_PROP_DECIMAL:
            fight_prop_val = round(fight_prop_val * 100, 1)
        else:
            fight_prop_val = round(fight_prop_val)

        emoji = ''
        if prop_id in FIGHT_PROP_EMOJIS:
            emoji = FIGHT_PROP_EMOJIS[prop_id] + ' | '

        msg += f"{emoji}{resolve_map_hash(text_map, v)}: {fight_prop_val}\n"
    """

    # We use `copy()` because `get_player_info()` is cached, and if we change
    # `showcase_characters` without using `copy()`, then
    # `player_info.player.showcase_characters` will also change
    # and will be returned every time we call `get_player_info()`
    show_avatar_info_list = player_info.player.showcase_characters.copy()
    logger.info(show_avatar_info_list)
    for avatar in show_avatar_info_list:
        if avatar.id == avatar_id:
            show_avatar_info_list.remove(avatar)
            break

    keyboard = await generate_avatars_kbd(
        caller_id, uid, show_avatar_info_list
    )
    await event.edit_message(msg, keyboard=keyboard)
