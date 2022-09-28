from vkbottle.bot import Blueprint, Message
from gacha_banner_vars import FALLBACK_ITEMS_5_POOL_1
from player_exists import exists
from utils import (
    get_banner_picture,
    resolve_id,
    get_textmap,
    get_banner,
    get_banners,
    get_banner_name,
    get_weapon_data,
    get_avatar_data
)
import create_pool

bp = Blueprint("Banners command")
bp.labeler.vbml_ignore_case = True

# Banners names
BANNERS_NAMES = {
    100: "Баннер новичка",
    301: "Ивент баннер 1",
    400: "Ивент баннер 2",
    200: "Стандартный баннер",
    302: "Баннер оружия",
}

# Each banner cache
banners_cache = {
    100: None,  # Баннер новичка
    301: None,  # Ивент баннер 1
    400: None,  # Ивент баннер 2
    200: None,  # Стандартный баннер
    302: None   # Баннер оружия
}

# List of banners cache
all_banners_cache = None


async def format_banners(raw_banner):
    new_msg = ""

    raw_avatars = await get_avatar_data()
    raw_weapons = await get_weapon_data()
    textmap = await get_textmap()

    if raw_banner['gachaType'] != 200:  # Not standard banner
        if raw_banner['rateUpItems5']:
            new_msg += f"{'&#11088;' * 5}\n"
            for rateupitem5 in raw_banner['rateUpItems5']:
                item = resolve_id(rateupitem5, raw_avatars, raw_weapons)
                item_name = textmap[str(item['nameTextMapHash'])]
                if rateupitem5 > 11100:  # Weapon
                    new_msg += f"&#128481; {item_name}\n"
                else:
                    new_msg += f"&#129485; {item_name}\n"
        else:
            new_msg += "\n"

        new_msg += f"{'&#11088;' * 4}\n"
        for rateupitem4 in raw_banner['rateUpItems4']:
            item = resolve_id(rateupitem4, raw_avatars, raw_weapons)
            item_name = textmap[str(item['nameTextMapHash'])]
            if rateupitem4 > 11100:  # Weapon
                new_msg += f"&#128481; {item_name}\n"
            else:
                new_msg += f"&#129485; {item_name}\n"
    else:  # Standard banner
        new_msg = f"{'&#11088;' * 5}\n"
        for item in FALLBACK_ITEMS_5_POOL_1:
            item = resolve_id(item, raw_avatars, raw_weapons)
            item_name = textmap[str(item['nameTextMapHash'])]
            new_msg += f"&#129485; {item_name}\n"

    banners_cache[raw_banner['gachaType']] = new_msg
    return new_msg


@bp.on.chat_message(text=(
    "!баннер",
    "!мой баннер",
    "!выбранный баннер",
    "!текущий баннер"
))
async def show_my_banner(message: Message):
    if not await exists(message):
        return

    pool = create_pool.pool
    async with pool.acquire() as pool:
        result = await pool.fetchrow(
            "SELECT current_banner FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )
        current_banner = result['current_banner']

    # Banner picture
    banner_picture = await get_banner_picture(current_banner)

    # Banner name
    banner_name = await get_banner_name(current_banner)

    # Banner fallback name
    banner_fallback_name = BANNERS_NAMES[current_banner]

    await message.answer(
        f"Ваш выбранный баннер: {banner_name} ({banner_fallback_name})",
        attachment=banner_picture
    )


@bp.on.chat_message(text="!баннеры")
async def show_all_banners(message: Message):
    if not await exists(message):
        return

    global all_banners_cache
    if all_banners_cache is not None:
        return all_banners_cache

    new_msg = "Список всех баннеров:\n"

    raw_banners = await get_banners()
    for raw_banner in raw_banners:
        try:
            new_msg += f"{BANNERS_NAMES[raw_banner['gachaType']]}: "
        except IndexError:
            new_msg += "Неизвестный баннер\n"
            continue

        banner_name = await get_banner_name(raw_banner['gachaType'])
        new_msg += f"{banner_name}\n"

    all_banners_cache = new_msg
    return new_msg


@bp.on.chat_message(text="!выбрать баннер <banner>")
async def choose_banner(message: Message, banner):
    if not await exists(message):
        return

    banners = {
        "новичка": 100,
        "ивент": 301,
        "ивент 1": 301,
        "ивент 2": 400,
        "стандарт": 200,
        "стандартный": 200,
        "оружейный": 302
    }

    if banner not in banners:
        return (
            "Такого баннера не существует!\n"
            "Могут быть только эти варианты: новичка, ивент, ивент 2, стандарт, оружейный"
        )

    choiced_banner = await get_banner(banners[banner])

    pool = create_pool.pool
    async with pool.acquire() as pool:
        await pool.execute(
            "UPDATE players SET current_banner=$1 WHERE user_id=$2 AND peer_id=$3",
            banners[banner], message.from_id, message.peer_id
        )

    banner_name = await get_banner_name(choiced_banner['gachaType'])
    return f'Вы выбрали баннер "{banner_name}"!'


@bp.on.chat_message(text="!баннер новичка")
async def show_noob_banner(message: Message):
    if not await exists(message):
        return

    gacha_type = 100
    picture = await get_banner_picture(gacha_type)
    if banners_cache[gacha_type] is not None:
        await message.answer(
            banners_cache[gacha_type],
            attachment=picture
        )
        return

    raw_banners = await get_banner(gacha_type)
    ans_msg = await format_banners(raw_banners)

    await message.answer(ans_msg, attachment=picture)


@bp.on.chat_message(text=(
    "!ив баннер <banner_id:int>",
    "!ивентовый баннер <banner_id:int>",
    "!баннер ивент <banner_id:int>",
    "!баннер ивент",
    "!ив баннер",
    "!ивентовый баннер",
))
async def show_event_banner(message: Message, banner_id: int = 1):
    if not await exists(message):
        return

    if banner_id == 1:
        gacha_type = 301
        picture = await get_banner_picture(gacha_type)
        if banners_cache[gacha_type] is not None:
            await message.answer(
                banners_cache[gacha_type],
                attachment=picture
            )
            return

        raw_banners = await get_banner(gacha_type)
    elif banner_id == 2:
        gacha_type = 400
        picture = await get_banner_picture(gacha_type)
        if banners_cache[gacha_type] is not None:
            await message.answer(
                banners_cache[gacha_type],
                attachment=picture
            )
            return

        raw_banners = await get_banner(gacha_type)
    else:
        return "Неправильный айди баннера!"

    ans_msg = await format_banners(raw_banners)

    await message.answer(
        ans_msg,
        attachment=picture
    )


@bp.on.chat_message(text=(
    "!оруж баннер",
    "!оружейный баннер",
    "!баннер оружия",
    "!баннер оружие",
    "!баннер оружейный",
    "!оружие баннер"
))
async def show_weapon_banner(message: Message):
    if not await exists(message):
        return

    gacha_type = 302
    picture = await get_banner_picture(gacha_type)
    if banners_cache[gacha_type] is not None:
        await message.answer(
            banners_cache[gacha_type],
            attachment=picture
        )
        return

    raw_banners = await get_banner(gacha_type)
    ans_msg = await format_banners(raw_banners)

    await message.answer(
        ans_msg,
        attachment=picture
    )


@bp.on.chat_message(text=(
    "!ст баннер",
    "!стандартный баннер",
    "!баннер стандарт<!>",
))
async def show_standard_banner(message: Message):
    if not await exists(message):
        return

    gacha_type = 200
    picture = await get_banner_picture(gacha_type)
    if banners_cache[gacha_type] is not None:
        await message.answer(
            banners_cache[gacha_type],
            attachment=picture
        )
        return

    raw_banners = await get_banner(gacha_type)
    ans_msg = await format_banners(raw_banners)

    await message.answer(
        ans_msg,
        attachment=picture
    )
