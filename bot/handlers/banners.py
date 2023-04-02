import os

import msgspec
from aiocache import cached
from loguru import logger
from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngImageFile
from vkbottle import Keyboard, Text
from vkbottle.bot import BotLabeler, Message
from vkbottle.tools import PhotoToAlbumUploader
from vkbottle.user import User

import create_pool
from config import BANNERS_ALBUM_ID, GROUP_ID, TEST_MODE, VK_USER_TOKEN
from gacha_banner_vars import FALLBACK_ITEMS_5_POOL_1
from keyboards import KEYBOARD_WISH
from models.banner import Banner, BannerType
from utils import (color_to_rarity, element_to_banner_bg, exists,
                   get_avatar_data, get_banner, get_banner_name, get_banners,
                   get_skill_depot_data, get_skill_excel_data, get_textmap,
                   get_weapon_data, resolve_id, resolve_map_hash, translate)

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
    100: None,  # Баннер новичка
    301: None,  # Ивент баннер 1
    400: None,  # Ивент баннер 2
    200: None,  # Стандартный баннер
    302: None   # Баннер оружия
}

# List of banners cache
all_banners_cache = None

banners_items_path = 'resources/banners_items/'
banners_bg_path = 'resources/banners_bg/'
banners_ui_path = 'resources/banners_ui/'
banners_cache_path = 'banners_cache/'

fnt_path = "resources/Genshin_Impact.ttf"
fnt = ImageFont.truetype(fnt_path, 45)
fnt_weapon = ImageFont.truetype(fnt_path, 42)
fnt_weapon_name = ImageFont.truetype(fnt_path, 28)


class BannerPicture:
    def __init__(
        self, bg: PngImageFile, main_rateup: PngImageFile, second_rateup: PngImageFile | None = None
    ):
        self.main_rateup = main_rateup
        self.second_rateup = second_rateup
        self.bg = bg
        self.star = Image.open(f"{banners_ui_path}star.png").resize((18, 18))

    def add_main_rateup_event(self):
        """Adds main rateup picture to event banner"""
        self.main_rateup.thumbnail((self.main_rateup.size[0], self.main_rateup.size[1]-75))

        bg_w, bg_h = self.bg.size
        im_w, im_h = self.main_rateup.size
        offset = ((bg_w - im_w)//2, (bg_h-im_h)//2+75)

        self.bg.paste(self.main_rateup, offset, self.main_rateup)

    def add_second_rateup_event(self):
        """Adds second rateup picture to event banner (4* characters)"""
        self.second_rateup.thumbnail((self.second_rateup.size[0], self.bg.size[1]))
        self.bg.paste(
            self.second_rateup, (self.bg.size[0]-self.second_rateup.size[0], 0), self.second_rateup
        )

    def add_main_rateup_weapon(self):
        """Adds main rateup picture to weapon banner"""
        if len(self.main_rateup) != 2:
            raise ValueError("Incorrect weapon rateup list count")

        bg_w, bg_h = self.bg.size
        size_change = 400
        x_change = 50
        y_change = 0
        for weapon in self.main_rateup:
            weapon.thumbnail((weapon.size[0], weapon.size[1]-size_change))

            im_w, im_h = weapon.size
            offset = ((bg_w - im_w)//2+x_change, (bg_h-im_h)//2-y_change)
            self.bg.paste(weapon, offset, weapon)
            size_change += 100
            x_change += 100
            y_change += 20

    def add_main_rateup_standard(self):
        """Adds main rateup picture to standard banner"""
        self.main_rateup.thumbnail((self.main_rateup.size[0], self.main_rateup.size[1]-300))
        bg_w, bg_h = self.bg.size
        im_w, im_h = self.main_rateup.size
        offset = ((bg_w-im_w)//2+140, (bg_h-im_h)//2-100)

        self.bg.paste(self.main_rateup, offset, self.main_rateup)

    def add_main_rateup_noob(self):
        """Adds main rateup picture to beginner's banner"""
        self.main_rateup.thumbnail((self.main_rateup.size[0], self.main_rateup.size[1]-75))

        bg_w, bg_h = self.bg.size
        im_w, im_h = self.main_rateup.size
        offset = ((bg_w - im_w)//2+154, (bg_h-im_h)//2+70)

        self.bg.paste(self.main_rateup, offset, self.main_rateup)

    def draw_outlined_text(self, text, x, y, fill_outline, fill, fnt):
        draw = ImageDraw.Draw(self.bg)

        # Draw outline
        draw.multiline_text((x-1, y-1), text, font=fnt, fill=fill_outline)
        draw.multiline_text((x+1, y-1), text, font=fnt, fill=fill_outline)
        draw.multiline_text((x-1, y+1), text, font=fnt, fill=fill_outline)
        draw.multiline_text((x+1, y+1), text, font=fnt, fill=fill_outline)

        # Draw text
        draw.multiline_text((x, y), text, font=fnt, fill=fill)

    def draw_banner_name(self, banner_name, x, y, fnt, do_wrap=True):
        fill = "#575356"
        outline_color = "white"

        if len(banner_name) > 10 and do_wrap:
            # Wrap banner name
            names_splitted = banner_name.split()
            for i in range(len(names_splitted)-1):
                if len(names_splitted[i])+len(names_splitted[i+1]) > 10:
                    names_splitted.insert(i+1, '\n')

            banner_name = ""
            for i in names_splitted:
                if i != "\n":
                    banner_name += i+" "
                else:
                    banner_name += i

        self.draw_outlined_text(banner_name, x, y, outline_color, fill, fnt)

    def draw_event_banner_name(self, banner_name):
        x, y = 40, 30
        self.draw_banner_name(banner_name, x, y, fnt)

    def draw_weapon_banner_name(self, banner_name):
        x, y = 40, 72
        self.draw_banner_name(banner_name, x, y, fnt)

    def draw_standard_banner_name(self, banner_name):
        x, y = 40, 30
        self.draw_banner_name(banner_name, x, y, fnt)

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
        self.draw_item_name(name, position[0], position[1], fnt)
        self.draw_stars(rarity, position[0], position[1]+60)

    def draw_weapon_name(self, names):
        position = [398, 356]
        self.draw_stars(5, position[0], position[1]+82)
        for i in names:
            self.draw_item_name(i, position[0], position[1], fnt_weapon_name)
            position[1] += 41

    def draw_noob_name(self, name, rarity):
        position = (591, 350)
        self.draw_stars(rarity, position[0], position[1]+57)
        self.draw_item_name(name, position[0], position[1], fnt)

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
            self.draw_stars(5, positions[i][0]-3, star_y)

    def save_banner(self, name):
        path = f'{banners_cache_path}{name}.jpg'
        self.bg = self.bg.convert('RGB')
        self.bg.save(path, quality=97)
        return path


async def get_main_rateup_picture(item_name):
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
    logger.warning(f"Picture of main rateup ({item_name}) not found!")


async def get_second_rateup_picture(banner_id):
    for filename in os.listdir(banners_items_path):
        if not filename.endswith('.png'):
            continue

        new_banner_id = filename.split('_')[2]
        if new_banner_id == banner_id:
            return filename


async def get_background_by_elem(element):
    for filename in os.listdir(banners_bg_path):
        if filename == f'UI_GachaShowPanel_Bg_{element}.png':
            return filename


async def check_banner_cache(prefab_path):
    logger.info(f"Checking if {prefab_path} exists in cache")
    pool = create_pool.pool
    async with pool.acquire() as pool:
        result = await pool.fetchrow(
            "SELECT picture_name, picture_id FROM pictures WHERE picture_name=$1",
            prefab_path
        )
    if result is not None:
        logger.info(f"Cache exists, results: {result}")
        return result


async def get_element(avatar_info):
    skill_depot_data = await get_skill_depot_data()
    skill_data = await get_skill_excel_data()

    skill_depot_id = avatar_info['skillDepotId']
    for skill_depot in skill_depot_data:
        if skill_depot['id'] == skill_depot_id:
            energy_skill = skill_depot['energySkill']
            for skill in skill_data:
                if skill['id'] == energy_skill:
                    return skill['costElemType']


async def create_banner(gacha_type) -> dict | None:
    if TEST_MODE:  # We don't generate banner, if test mode is true
        return

    # Return cache if exists
    banner: Banner = await get_banner(gacha_type)
    prefab_path = banner.prefab_path
    banner_cache = await check_banner_cache(prefab_path)
    if banner_cache is not None:
        return {"attachment": banner_cache['picture_id']}

    avatar_data = await get_avatar_data()
    weapon_data = await get_weapon_data()
    textmap = await get_textmap()

    banner_type = banner.banner_type
    banner_name = await get_banner_name(gacha_type)
    rateup5 = banner.rate_up_items_5
    rateup4 = banner.rate_up_items_4

    # TODO: How to make this cleaner?
    match banner_type:
        case BannerType.EVENT:
            if rateup5 is None or len(rateup5) == 0:
                # Beginner's banner
                rateup4 = rateup4[0]
                item_info = resolve_id(rateup4, avatar_data)
                element = await get_element(item_info)
                element = element_to_banner_bg(element)
                banner_bg = await get_background_by_elem(element)
                main_rateup = await get_main_rateup_picture(item_info['iconName'].split('_')[2])
                main_rateup_name = resolve_map_hash(textmap, item_info['nameTextMapHash'])
                main_rateup_rarity = color_to_rarity(item_info['qualityType'])

                banner_bg = Image.open(f"{banners_bg_path}{banner_bg}")
                main_rateup = Image.open(f"{banners_items_path}{main_rateup}")

                banner_picture = BannerPicture(banner_bg, main_rateup)
                banner_picture.add_main_rateup_noob()
                banner_picture.draw_event_banner_name(banner_name)
                banner_picture.draw_noob_box()
                banner_picture.draw_noob_name(main_rateup_name, main_rateup_rarity)
            else:
                # Character banner
                rateup5 = rateup5[0]
                item_info = resolve_id(rateup5, avatar_data)
                element = await get_element(item_info)
                element = element_to_banner_bg(element)
                banner_bg = await get_background_by_elem(element)
                main_rateup = await get_main_rateup_picture(item_info['iconName'].split('_')[2])
                second_rateup = await get_second_rateup_picture(banner.prefab_path.split('_')[1])
                main_rateup_name = resolve_map_hash(textmap, item_info['nameTextMapHash'])
                main_rateup_rarity = color_to_rarity(item_info['qualityType'])

                if main_rateup is None or second_rateup is None:
                    return {
                        "error": (
                            "В данный момент невозможно сгенерировать "
                            "баннер, попробуйте позже!\n"
                            f"item_info id: {item_info.get('id')}"
                        )
                    }

                banner_bg = Image.open(f"{banners_bg_path}{banner_bg}")
                main_rateup = Image.open(f"{banners_items_path}{main_rateup}")
                second_rateup = Image.open(f"{banners_items_path}{second_rateup}")

                banner_picture = BannerPicture(banner_bg, main_rateup, second_rateup)
                banner_picture.add_main_rateup_event()
                banner_picture.add_second_rateup_event()
                banner_picture.draw_event_banner_name(banner_name)
                banner_picture.draw_event_box()
                banner_picture.draw_event_name(main_rateup_name, main_rateup_rarity)

        case BannerType.WEAPON:
            # Weapon banner
            # TODO: Use rateup 4
            banner_bg = "UI_GachaShowPanel_Bg_Weapon.png"
            main_rateup1 = rateup5[0]
            main_rateup2 = rateup5[1]
            rateup1_info = resolve_id(main_rateup1, weapon_data=weapon_data)
            rateup2_info = resolve_id(main_rateup2, weapon_data=weapon_data)
            rateup1_name = resolve_map_hash(textmap, rateup1_info['nameTextMapHash'])
            rateup2_name = resolve_map_hash(textmap, rateup2_info['nameTextMapHash'])
            main_rateup1 = await get_main_rateup_picture(
                '_'.join(rateup1_info['icon'].split('_')[2:4])
            )
            main_rateup2 = await get_main_rateup_picture(
                '_'.join(rateup2_info['icon'].split('_')[2:4])
            )

            banner_bg = Image.open(f"{banners_bg_path}{banner_bg}")
            main_rateup1 = Image.open(f"{banners_items_path}{main_rateup1}")
            main_rateup2 = Image.open(f"{banners_items_path}{main_rateup2}")

            banner_picture = BannerPicture(banner_bg, (main_rateup1, main_rateup2))
            banner_picture.add_main_rateup_weapon()
            banner_picture.draw_weapon_banner_name(banner_name)
            banner_picture.draw_weapon_box()
            banner_picture.draw_weapon_name((rateup1_name, rateup2_name))

        case _:
            # Standard banner
            banner_bg = "UI_GachaShowPanel_Bg_Nomal.png"
            items_show = (
                1042,  # Keqing
                1041,  # Mona
                1035,  # Qiqi
            )
            items_names = []
            for i in items_show:
                item_info = resolve_id(i, avatar_data)
                item_name = resolve_map_hash(textmap, item_info['nameTextMapHash'])
                items_names.append(item_name)
            rateup_picture = await get_second_rateup_picture(banner['prefabPath'].split('_')[1])

            banner_bg = Image.open(f"{banners_bg_path}{banner_bg}")
            main_rateup = Image.open(f"{banners_items_path}{rateup_picture}")

            banner_picture = BannerPicture(banner_bg, main_rateup)
            banner_picture.add_main_rateup_standard()
            banner_picture.draw_standard_banner_name(banner_name)
            banner_picture.draw_standard_boxes()
            banner_picture.draw_standard_names(items_names)

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
            prefab_path, banner_attachment
        )
    return {"attachment": banner_attachment}


@cached()
async def format_banners(banner: Banner):
    new_msg = ""

    raw_avatars = await get_avatar_data()
    raw_weapons = await get_weapon_data()
    textmap = await get_textmap()

    if banner.gacha_type != 200:  # Not standard banner
        if banner.rate_up_items_5:
            new_msg += f"{'&#11088;' * 5}\n"
            for rateupitem5 in banner.rate_up_items_5:
                item = resolve_id(rateupitem5, raw_avatars, raw_weapons)

                if item is None:
                    new_msg += "? Неизвестный предмет\n"
                    continue

                item_name = textmap[str(item['nameTextMapHash'])]
                if rateupitem5 > 11100:  # Weapon
                    new_msg += f"&#128481; {item_name}\n"
                else:
                    new_msg += f"&#129485; {item_name}\n"
        else:
            new_msg += "\n"

        new_msg += f"{'&#11088;' * 4}\n"
        for rateupitem4 in banner.rate_up_items_4:
            item = resolve_id(rateupitem4, raw_avatars, raw_weapons)

            if item is None:
                new_msg += "? Неизвестный предмет\n"
                continue

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

    banners_cache[banner.gacha_type] = new_msg
    return new_msg


KEYBOARD_BEGINNER = (
    Keyboard(inline=True)
    .add(Text("Выбрать баннер новичка"))
)
KEYBOARD_EVENT = (
    Keyboard(inline=True)
    .add(Text("Выбрать баннер ивент"))
)
KEYBOARD_EVENT_SECOND = (
    Keyboard(inline=True)
    .add(Text("Выбрать баннер ивент 2"))
)
KEYBOARD_WEAPON = (
    Keyboard(inline=True)
    .add(Text("Выбрать баннер оружие"))
)
KEYBOARD_STANDARD = (
    Keyboard(inline=True)
    .add(Text("Выбрать баннер стандарт"))
)


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
        return banner_attachment["error"]
    banner_attachment = banner_attachment.get("attachment")

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

    new_msg = (await translate("banners", "list"))+"\n"

    raw_banners = await get_banners()
    decoder = msgspec.json.Decoder(Banner)
    encoder = msgspec.json.Encoder()
    for raw_banner in raw_banners:
        # Converting to json
        banner = encoder.encode(raw_banner)
        # Converting to `Banner` object
        banner = decoder.decode(banner)
        try:
            new_msg += f"{BANNERS_NAMES[banner.gacha_type]}: "
        except IndexError:
            new_msg += (await translate("banners", "unknown_banner"))+"\n"
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

    choiced_banner: Banner = await get_banner(banners[banner])

    pool = create_pool.pool
    async with pool.acquire() as pool:
        await pool.execute(
            "UPDATE players SET current_banner=$1 WHERE user_id=$2 AND peer_id=$3",
            banners[banner], message.from_id, message.peer_id
        )

    banner_name = await get_banner_name(choiced_banner.gacha_type)
    banner_attachment = await create_banner(choiced_banner.gacha_type) or {}
    if banner_attachment.get("error"):
        return banner_attachment["error"]
    banner_attachment = banner_attachment.get("attachment")

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
    banner_attachment = await create_banner(gacha_type) or {}
    if banner_attachment.get("error"):
        return banner_attachment["error"]
    banner_attachment = banner_attachment.get("attachment")

    if banners_cache[gacha_type] is not None:
        ans_msg = banners_cache[gacha_type]
    else:
        raw_banners = await get_banner(gacha_type)
        ans_msg = await format_banners(raw_banners)

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

    banner_attachment = await create_banner(gacha_type) or {}
    if banner_attachment.get("error"):
        return banner_attachment["error"]
    banner_attachment = banner_attachment.get("attachment")

    if banners_cache[gacha_type] is not None:
        ans_msg = banners_cache[gacha_type]
    else:
        raw_banners = await get_banner(gacha_type)
        ans_msg = await format_banners(raw_banners)

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
    banner_attachment = await create_banner(gacha_type) or {}
    if banner_attachment.get("error"):
        return banner_attachment["error"]
    banner_attachment = banner_attachment.get("attachment")

    if banners_cache[gacha_type] is not None:
        ans_msg = banners_cache[gacha_type]
    else:
        raw_banners = await get_banner(gacha_type)
        ans_msg = await format_banners(raw_banners)

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
    banner_attachment = await create_banner(gacha_type) or {}
    if banner_attachment.get("error"):
        return banner_attachment["error"]
    banner_attachment = banner_attachment.get("attachment")

    if banners_cache[gacha_type] is not None:
        ans_msg = banners_cache[gacha_type]
    else:
        raw_banners = await get_banner(gacha_type)
        ans_msg = await format_banners(raw_banners)

    await message.answer(
        ans_msg,
        attachment=banner_attachment,
        keyboard=KEYBOARD_STANDARD
    )
