import os

from PIL import ImageDraw, ImageFont, Image
from PIL.Image import Image as ImageType
from aiocache import cached
from loguru import logger
from vkbottle.bot import BotLabeler, Message
from vkbottle.tools import PhotoToAlbumUploader
from vkbottle.user import User

import create_pool
from config import BANNERS_ALBUM_ID, GROUP_ID, VK_USER_TOKEN
from gacha_banner_vars import FALLBACK_ITEMS_5_POOL_1
from keyboards import (
    KEYBOARD_BEGINNER,
    KEYBOARD_EVENT,
    KEYBOARD_EVENT_SECOND,
    KEYBOARD_STANDARD,
    KEYBOARD_WEAPON,
    KEYBOARD_WISH
)
from models.avatar import Avatar
from models.banner import Banner, BannerType
from models.weapon import Weapon
from utils import (
    exists,
    get_avatar_data,
    get_banner,
    get_banner_name,
    get_banners,
    get_text_map,
    get_weapon_data,
    resolve_id,
    resolve_map_hash,
    translate
)

bl = BotLabeler()
bl.vbml_ignore_case = True
user = User(VK_USER_TOKEN)

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
    100: "",  # Баннер новичка
    301: "",  # Ивент баннер 1
    400: "",  # Ивент баннер 2
    200: "",  # Стандартный баннер
    302: ""  # Баннер оружия
}

all_banners_cache = None

banners_items_path = 'resources/banners_items/'
banners_bg_path = 'resources/banners_bg/'
banners_ui_path = 'resources/banners_ui/'
banners_cache_path = 'banners_cache/'

fnt_path = "resources/Genshin_Impact.ttf"
fnt_default = ImageFont.truetype(fnt_path, 45)
fnt_weapon = ImageFont.truetype(fnt_path, 42)
fnt_weapon_name = ImageFont.truetype(fnt_path, 28)


class BannerPicture:
    def __init__(
        self, bg: Image, main_rate_up: ImageType | tuple[ImageType, ImageType],
        second_rate_up: ImageType | None = None
    ):
        self.main_rate_up = main_rate_up
        self.second_rate_up = second_rate_up
        self.bg = bg
        self.star = Image.open(f"{banners_ui_path}star.png").resize((18, 18))

    def add_main_rate_up_event(self):
        """Adds main rate up picture to event banner"""
        self.main_rate_up.thumbnail((self.main_rate_up.size[0], self.main_rate_up.size[1] - 75))

        bg_w, bg_h = self.bg.size
        im_w, im_h = self.main_rate_up.size
        offset = ((bg_w - im_w) // 2, (bg_h - im_h) // 2 + 75)

        self.bg.paste(self.main_rate_up, offset, self.main_rate_up)

    def add_second_rate_up_event(self):
        """Adds second rate up picture to event banner (4* characters)"""
        self.second_rate_up.thumbnail((self.second_rate_up.size[0], self.bg.size[1]))
        self.bg.paste(
            self.second_rate_up, (self.bg.size[0] - self.second_rate_up.size[0], 0),
            self.second_rate_up
        )

    def add_main_rate_up_weapon(self):
        """Adds main rate up picture to weapon banner"""
        if len(self.main_rate_up) != 2:
            raise ValueError("Incorrect weapon rate_up list count")

        bg_w, bg_h = self.bg.size
        size_change = 400
        x_change = 50
        y_change = 0
        for weapon in self.main_rate_up:
            weapon.thumbnail((weapon.size[0], weapon.size[1] - size_change))

            im_w, im_h = weapon.size
            offset = ((bg_w - im_w) // 2 + x_change, (bg_h - im_h) // 2 - y_change)
            self.bg.paste(weapon, offset, weapon)
            size_change += 100
            x_change += 100
            y_change += 20

    def add_main_rate_up_standard(self):
        """Adds main rate up picture to standard banner"""
        self.main_rate_up.thumbnail((self.main_rate_up.size[0], self.main_rate_up.size[1] - 300))
        bg_w, bg_h = self.bg.size
        im_w, im_h = self.main_rate_up.size
        offset = ((bg_w - im_w) // 2 + 140, (bg_h - im_h) // 2 - 100)

        self.bg.paste(self.main_rate_up, offset, self.main_rate_up)

    def add_main_rate_up_noob(self):
        """Adds main rate up picture to beginner's banner"""
        self.main_rate_up.thumbnail((self.main_rate_up.size[0], self.main_rate_up.size[1] - 75))

        bg_w, bg_h = self.bg.size
        im_w, im_h = self.main_rate_up.size
        offset = ((bg_w - im_w) // 2 + 154, (bg_h - im_h) // 2 + 70)

        self.bg.paste(self.main_rate_up, offset, self.main_rate_up)

    def draw_outlined_text(self, text, x, y, fill_outline, fill, fnt):
        draw = ImageDraw.Draw(self.bg)

        # Draw outline
        draw.multiline_text((x - 1, y - 1), text, font=fnt, fill=fill_outline)
        draw.multiline_text((x + 1, y - 1), text, font=fnt, fill=fill_outline)
        draw.multiline_text((x - 1, y + 1), text, font=fnt, fill=fill_outline)
        draw.multiline_text((x + 1, y + 1), text, font=fnt, fill=fill_outline)

        # Draw text
        draw.multiline_text((x, y), text, font=fnt, fill=fill)

    def draw_banner_name(self, banner_name, x, y, fnt, do_wrap=True):
        fill = "#575356"
        outline_color = "white"

        if len(banner_name) > 10 and do_wrap:
            # Wrap banner name
            names_splintered = banner_name.split()
            for i in range(len(names_splintered) - 1):
                if len(names_splintered[i]) + len(names_splintered[i + 1]) > 10:
                    names_splintered.insert(i + 1, '\n')

            banner_name = ""
            for i in names_splintered:
                if i != "\n":
                    banner_name += i + " "
                else:
                    banner_name += i

        self.draw_outlined_text(banner_name, x, y, outline_color, fill, fnt)

    def draw_event_banner_name(self, banner_name):
        x, y = 40, 30
        self.draw_banner_name(banner_name, x, y, fnt_default)

    def draw_weapon_banner_name(self, banner_name):
        x, y = 40, 72
        self.draw_banner_name(banner_name, x, y, fnt_default)

    def draw_standard_banner_name(self, banner_name):
        x, y = 40, 30
        self.draw_banner_name(banner_name, x, y, fnt_default)

    def draw_item_name(self, name, x, y, fnt):
        fill = "white"
        outline_color = "#575356"

        self.draw_outlined_text(name, x, y, outline_color, fill, fnt)

    def draw_stars(self, rarity, x, y):
        for _ in range(rarity):
            self.bg.paste(self.star, (x, y), self.star)
            x += 20

    def draw_rectangle(self, boxes):
        # https://stackoverflow.com/questions/43618910/pil-drawing-a-semi-transparent-square-overlay-on-image#43620169
        overlay = Image.new('RGBA', self.bg.size)
        draw = ImageDraw.Draw(overlay)

        for i in boxes:
            draw.rectangle(i, fill=(0, 0, 0, 170))

        self.bg = Image.alpha_composite(self.bg, overlay)

    def draw_event_box(self):
        box = [(554, 380, 789, 439)]
        self.draw_rectangle(box)

    def draw_weapon_box(self):
        box = [(389, 374, 689, 461)]
        return self.draw_rectangle(box)

    def draw_standard_boxes(self):
        boxes = [
            (591, 288, 810, 342),  # Keqing
            (449, 130, 631, 161),  # Mona
            (351, 422, 541, 453),  # Qiqi
        ]
        return self.draw_rectangle(boxes)

    def draw_noob_box(self):
        box = [(554, 380, 807, 430)]
        self.draw_rectangle(box)

    def draw_event_name(self, name, rarity):
        position = (591, 360)
        self.draw_item_name(name, position[0], position[1], fnt_default)
        self.draw_stars(rarity, position[0], position[1] + 60)

    def draw_weapon_name(self, names):
        position = [398, 356]
        self.draw_stars(5, position[0], position[1] + 82)
        for i in names:
            self.draw_item_name(i, position[0], position[1], fnt_weapon_name)
            position[1] += 41

    def draw_noob_name(self, name, rarity):
        position = (591, 350)
        self.draw_stars(rarity, position[0], position[1] + 57)
        self.draw_item_name(name, position[0], position[1], fnt_default)

    def draw_standard_names(self, names):
        if len(names) != 3:
            raise ValueError("Wrong list of standard characters")

        fnt_main = ImageFont.truetype(fnt_path, 45)
        fnt_others = ImageFont.truetype(fnt_path, 29)

        positions = [
            (627, 260),
            (478, 102),
            (380, 393)
        ]
        for i in range(len(positions)):
            star_y = positions[i][1]
            if i == 0:
                star_y += 60
                current_fnt = fnt_main
            else:
                star_y += 37
                current_fnt = fnt_others

            self.draw_item_name(names[i], positions[i][0], positions[i][1], current_fnt)
            self.draw_stars(5, positions[i][0] - 3, star_y)

    def save_banner(self, name):
        path = f'{banners_cache_path}{name}.jpg'
        self.bg = self.bg.convert('RGB')
        self.bg.save(path, quality=97)
        return path


async def get_main_rate_up_picture(item_name: str):
    for filename in os.listdir(banners_items_path):
        if not filename.endswith('.png'):
            continue
        filename = filename.replace('.png', '')

        name = ''
        if filename.startswith('UI_Gacha_AvatarImg_'):
            name = filename.split('_')[3]
        elif filename.startswith('UI_Gacha_EquipIcon_'):
            name = '_'.join(filename.split('_')[3:5])

        filename += '.png'

        if item_name.lower() == name.lower():
            return filename
    logger.warning(f"Picture of main rate up ({item_name}) not found!")


async def get_second_rate_up_picture(banner_id: str):
    for filename in os.listdir(banners_items_path):
        if not filename.endswith('.png'):
            continue

        new_banner_id = filename.split('_')[2]
        if new_banner_id == banner_id:
            return filename


async def get_background_by_elem(element: str) -> str | None:
    for filename in os.listdir(banners_bg_path):
        if filename == f'UI_GachaShowPanel_Bg_{element}.png':
            return filename


async def check_banner_cache(prefab_id):
    logger.info(f"Checking if {prefab_id} exists in cache")
    pool = create_pool.pool
    async with pool.acquire() as pool:
        result = await pool.fetchrow(
            "SELECT picture_name, picture_id FROM pictures WHERE picture_name=$1",
            prefab_id
        )
    if result is not None:
        logger.info(f"Cache exists, results: {result}")
        return result


async def create_banner(gacha_type) -> dict | None:
    # Return cache if exists
    banner: Banner = await get_banner(gacha_type)
    prefab_id = banner.prefab_id
    banner_cache = await check_banner_cache(prefab_id)
    if banner_cache is not None:
        return {"attachment": banner_cache['picture_id']}

    avatar_data = await get_avatar_data()
    weapon_data = await get_weapon_data()
    text_map = await get_text_map()

    banner_type = banner.banner_type
    banner_name = await get_banner_name(gacha_type)
    rate_up5 = banner.rate_up_5
    rate_up4 = banner.rate_up_4

    # TODO: How to make this cleaner?
    match banner_type:
        case BannerType.EVENT:
            if rate_up5 is None or len(rate_up5) == 0:
                # Beginner's banner
                rate_up4 = rate_up4[0]
                avatar: Avatar = resolve_id(rate_up4, avatar_data)
                element = avatar.element.value
                banner_bg = await get_background_by_elem(element)
                main_rate_up_picture_path = avatar.gacha_img
                main_rate_up_name = resolve_map_hash(text_map, avatar.name_text_map_hash)
                main_rate_up_rarity = avatar.quality

                banner_bg = Image.open(f"{banners_bg_path}{banner_bg}")
                main_rate_up_picture = Image.open(
                    f"{banners_items_path}{main_rate_up_picture_path}"
                )

                banner_picture = BannerPicture(banner_bg, main_rate_up_picture)
                banner_picture.add_main_rate_up_noob()
                banner_picture.draw_event_banner_name(banner_name)
                banner_picture.draw_noob_box()
                banner_picture.draw_noob_name(main_rate_up_name, main_rate_up_rarity)
            else:
                # Character banner
                rate_up5 = rate_up5[0]
                avatar: Avatar = resolve_id(rate_up5, avatar_data)
                element = avatar.element.value
                banner_bg = await get_background_by_elem(element)
                main_rate_up_picture_path = avatar.gacha_img
                second_rate_up_picture_path = await get_second_rate_up_picture(banner.prefab_id)
                main_rate_up_name = resolve_map_hash(text_map, avatar.name_text_map_hash)
                main_rate_up_rarity = avatar.quality

                if main_rate_up_picture_path is None or second_rate_up_picture_path is None:
                    logger.error("Couldn't find main/second rate up picture for banner")
                    return {
                        "error": (
                            "В данный момент невозможно сгенерировать "
                            "баннер, попробуйте позже!\n"
                            f"avatar id: {avatar.id}"
                        )
                    }

                banner_bg = Image.open(f"{banners_bg_path}{banner_bg}")
                main_rate_up_picture = Image.open(
                    f"{banners_items_path}{main_rate_up_picture_path}"
                )
                second_rate_up_picture = Image.open(
                    f"{banners_items_path}{second_rate_up_picture_path}"
                )

                banner_picture = BannerPicture(
                    banner_bg, main_rate_up_picture, second_rate_up_picture
                )
                banner_picture.add_main_rate_up_event()
                banner_picture.add_second_rate_up_event()
                banner_picture.draw_event_banner_name(banner_name)
                banner_picture.draw_event_box()
                banner_picture.draw_event_name(main_rate_up_name, main_rate_up_rarity)

        case BannerType.WEAPON:
            # Weapon banner
            # TODO: Use rate up 4
            banner_bg = "UI_GachaShowPanel_Bg_Weapon.png"
            main_rate_up1 = rate_up5[0]
            main_rate_up2 = rate_up5[1]
            weapon1: Weapon = resolve_id(main_rate_up1, weapon_data=weapon_data)
            weapon2: Weapon = resolve_id(main_rate_up2, weapon_data=weapon_data)
            weapon1_name = resolve_map_hash(text_map, weapon1.name_text_map_hash)
            weapon2_name = resolve_map_hash(text_map, weapon2.name_text_map_hash)
            weapon1_picture_path = weapon1.gacha_img
            weapon2_picture_path = weapon2.gacha_img

            banner_bg = Image.open(f"{banners_bg_path}{banner_bg}")
            weapon1_picture = Image.open(f"{banners_items_path}{weapon1_picture_path}")
            weapon2_picture = Image.open(f"{banners_items_path}{weapon2_picture_path}")

            banner_picture = BannerPicture(banner_bg, (weapon1_picture, weapon2_picture))
            banner_picture.add_main_rate_up_weapon()
            banner_picture.draw_weapon_banner_name(banner_name)
            banner_picture.draw_weapon_box()
            banner_picture.draw_weapon_name((weapon1_name, weapon2_name))

        case _:
            # Standard banner
            banner_bg = "UI_GachaShowPanel_Bg_Nomal.png"
            avatars_show = (
                1042,  # Keqing
                1041,  # Mona
                1035,  # Qiqi
            )
            avatars_names = []
            for i in avatars_show:
                avatar: Avatar = resolve_id(i, avatar_data)
                avatar_name = resolve_map_hash(text_map, avatar.name_text_map_hash)
                avatars_names.append(avatar_name)
            rate_up_picture_path = await get_second_rate_up_picture(banner.prefab_id)

            banner_bg = Image.open(f"{banners_bg_path}{banner_bg}")
            main_rate_up_picture = Image.open(f"{banners_items_path}{rate_up_picture_path}")

            banner_picture = BannerPicture(banner_bg, main_rate_up_picture)
            banner_picture.add_main_rate_up_standard()
            banner_picture.draw_standard_banner_name(banner_name)
            banner_picture.draw_standard_boxes()
            banner_picture.draw_standard_names(avatars_names)

    # Saving image to local storage and group album
    banner_result = banner_picture.save_banner(f"banner_{gacha_type}")
    banner_attachment = (await PhotoToAlbumUploader(user.api).upload(
        group_id=GROUP_ID, album_id=BANNERS_ALBUM_ID, paths_like=banner_result
    ))[0]
    pool = create_pool.pool
    async with pool.acquire() as pool:
        await pool.execute(
            "INSERT INTO pictures (picture_name, picture_id) "
            "VALUES ($1, $2)",
            prefab_id, banner_attachment
        )
    return {"attachment": banner_attachment}


@cached()
async def format_banner(banner: Banner):
    new_msg = ""

    raw_avatars = await get_avatar_data()
    raw_weapons = await get_weapon_data()
    text_map = await get_text_map()

    if banner.gacha_type != 200:  # Not a standard banner
        if banner.rate_up_5:
            new_msg += f"{'&#11088;' * 5}\n"
            for rate_up_item5 in banner.rate_up_5:
                item = resolve_id(rate_up_item5, raw_avatars, raw_weapons)

                if item is None:
                    new_msg += "? Неизвестный предмет\n"
                    continue

                item_name = text_map[str(item.name_text_map_hash)]
                if rate_up_item5 > 11100:  # Weapon
                    new_msg += f"&#128481; {item_name}\n"
                else:
                    new_msg += f"&#129485; {item_name}\n"
        else:
            new_msg += "\n"

        new_msg += f"{'&#11088;' * 4}\n"
        for rate_up_item4 in banner.rate_up_4:
            item = resolve_id(rate_up_item4, raw_avatars, raw_weapons)

            if item is None:
                new_msg += "? Неизвестный предмет\n"
                continue

            item_name = text_map[str(item.name_text_map_hash)]
            if rate_up_item4 > 11100:  # Weapon
                new_msg += f"&#128481; {item_name}\n"
            else:
                new_msg += f"&#129485; {item_name}\n"
    else:  # Standard banner
        new_msg = f"{'&#11088;' * 5}\n"
        for item_id in FALLBACK_ITEMS_5_POOL_1:
            item = resolve_id(item_id, raw_avatars, raw_weapons)
            if item is None:
                logger.error(f"Banner item not found (id {item_id})")
                continue
            item_name = text_map[str(item.name_text_map_hash)]
            new_msg += f"&#129485; {item_name}\n"

    banners_cache[banner.gacha_type] = new_msg
    return new_msg


@bl.message(text=(
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
    banner_attachment = await create_banner(current_banner) or {}
    if banner_attachment.get("error"):
        logger.error(f"Couldn't get attachment: {banner_attachment['error']}")
    banner_attachment = banner_attachment.get("attachment", None)

    # Banner name
    banner_name = await get_banner_name(current_banner)

    # Banner fallback name
    banner_fallback_name = BANNERS_NAMES[current_banner]

    await message.answer(
        (
            await translate("banners", "current")
        ).format(banner_name=banner_name, banner_fallback_name=banner_fallback_name),
        attachment=banner_attachment,
        keyboard=KEYBOARD_WISH
    )


@bl.message(text="!баннеры")
async def show_all_banners(message: Message):
    if not await exists(message):
        return

    global all_banners_cache
    if all_banners_cache is not None:
        return all_banners_cache

    new_msg = (await translate("banners", "list")) + "\n"

    banners = await get_banners()
    for banner in banners:
        try:
            new_msg += f"{BANNERS_NAMES[banner.gacha_type]}: "
        except IndexError:
            new_msg += (await translate("banners", "unknown_banner")) + "\n"
            continue

        banner_name = await get_banner_name(banner.gacha_type, add_main=True)
        new_msg += f"{banner_name}\n"

    all_banners_cache = new_msg
    return new_msg


@bl.message(text=(
    "!выбрать баннер <banner>",
    "[<!>|<!>] Выбрать баннер <banner>",
    "Выбрать баннер <banner>",
))
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
        "оружейный": 302,
        "оружие": 302,
    }

    if banner not in banners:
        return await translate("banners", "selected_unknown")

    selected_banner: Banner | None = await get_banner(banners[banner])
    if selected_banner is None:
        logger.error(f"Known banner not found (gacha_type {banners[banner]})")
        return await translate("banners", "unknown_banner")

    pool = create_pool.pool
    async with pool.acquire() as pool:
        await pool.execute(
            "UPDATE players SET current_banner=$1 WHERE user_id=$2 AND peer_id=$3",
            banners[banner], message.from_id, message.peer_id
        )

    # Banner picture
    banner_name = await get_banner_name(selected_banner.gacha_type)
    banner_attachment = await create_banner(selected_banner.gacha_type) or {}
    if banner_attachment.get("error"):
        logger.error(f"Couldn't get attachment: {banner_attachment['error']}")
    banner_attachment = banner_attachment.get("attachment", None)

    await message.answer(
        (await translate("banners", "selected")).format(banner_name=banner_name),
        attachment=banner_attachment,
        keyboard=KEYBOARD_WISH
    )


@bl.message(text=(
    "!баннер новичк<!>",
    "!баннер нуба"
))
async def show_beginner_banner(message: Message):
    if not await exists(message):
        return
    gacha_type = 100

    # Banner picture
    banner_attachment = await create_banner(gacha_type) or {}
    if banner_attachment.get("error"):
        logger.error(f"Couldn't get attachment: {banner_attachment['error']}")
    banner_attachment = banner_attachment.get("attachment", None)

    if banners_cache[gacha_type]:
        ans_msg = banners_cache[gacha_type]
    else:
        banner = await get_banner(gacha_type)
        ans_msg = await format_banner(banner)

    await message.answer(
        ans_msg, attachment=banner_attachment, keyboard=KEYBOARD_BEGINNER
    )


@bl.message(text=(
    "!ив баннер <banner_id:int>",
    "!ивентовый баннер <banner_id:int>",
    "!баннер ивент <banner_id:int>",
    "!баннер ивент",
    "!ив баннер",
    "!ивентовый баннер"
))
async def show_event_banner(message: Message, banner_id: int = 1):
    if not await exists(message):
        return

    if banner_id == 1:
        gacha_type = 301
    elif banner_id == 2:
        gacha_type = 400
    else:
        return await translate("banners", "unknown_id")

    # Banner picture
    banner_attachment = await create_banner(gacha_type) or {}
    if banner_attachment.get("error"):
        logger.error(f"Couldn't get attachment: {banner_attachment['error']}")
    banner_attachment = banner_attachment.get("attachment", None)

    if banners_cache[gacha_type]:
        ans_msg = banners_cache[gacha_type]
    else:
        banner = await get_banner(gacha_type)
        ans_msg = await format_banner(banner)

    await message.answer(
        ans_msg,
        attachment=banner_attachment,
        keyboard=(KEYBOARD_EVENT if banner_id == 1 else KEYBOARD_EVENT_SECOND)
    )


@bl.message(text=(
    "!оруж баннер",
    "!оружейный баннер",
    "!баннер оруж<!>",
    "!оружие баннер"
))
async def show_weapon_banner(message: Message):
    if not await exists(message):
        return
    gacha_type = 302

    # Banner picture
    banner_attachment = await create_banner(gacha_type) or {}
    if banner_attachment.get("error"):
        logger.error(f"Couldn't get attachment: {banner_attachment['error']}")
    banner_attachment = banner_attachment.get("attachment", None)

    if banners_cache[gacha_type]:
        ans_msg = banners_cache[gacha_type]
    else:
        banner = await get_banner(gacha_type)
        ans_msg = await format_banner(banner)

    await message.answer(
        ans_msg,
        attachment=banner_attachment,
        keyboard=KEYBOARD_WEAPON
    )


@bl.message(text=(
    "!ст баннер",
    "!стандартный баннер",
    "!баннер стандарт<!>",
))
async def show_standard_banner(message: Message):
    if not await exists(message):
        return
    gacha_type = 200

    # Banner picture
    banner_attachment = await create_banner(gacha_type) or {}
    if banner_attachment.get("error"):
        logger.error(f"Couldn't get attachment: {banner_attachment['error']}")
    banner_attachment = banner_attachment.get("attachment", None)

    if banners_cache[gacha_type]:
        ans_msg = banners_cache[gacha_type]
    else:
        banner = await get_banner(gacha_type)
        ans_msg = await format_banner(banner)

    await message.answer(
        ans_msg,
        attachment=banner_attachment,
        keyboard=KEYBOARD_STANDARD
    )
