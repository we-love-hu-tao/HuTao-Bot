import asyncio
import random
import time
from typing import Literal

import msgspec
from loguru import logger
from vkbottle.bot import Blueprint, Message
from vkbottle_types.objects import UsersUserFull

import create_pool
from gacha_banner_vars import (EVENT_BANNERS, FALLBACK_ITEMS_3,
                               FALLBACK_ITEMS_4_POOL_1,
                               FALLBACK_ITEMS_4_POOL_2,
                               FALLBACK_ITEMS_5_POOL_1,
                               FALLBACK_ITEMS_5_POOL_2, POOL_BALANCE_WEIGHTS4,
                               POOL_BALANCE_WEIGHTS5, STANDARD_BANNERS,
                               STARDUST_ID, STARGLITTER_ID, WEIGHTS4, WEIGHTS5)
from utils import (color_to_rarity, exists, get_avatar_data, get_banner_name,
                   get_banners, get_item, get_textmap, get_weapon_data,
                   give_avatar, give_item_local, resolve_id)
from variables import (FIVE_STAR, FIVE_STAR_TEN, FOUR_STAR, FOUR_STAR_TEN,
                       THREE_STAR)

bp = Blueprint("Use wish")
bp.labeler.vbml_ignore_case = True


# Following code is based on https://github.com/Grasscutters/Grasscutter/
class Wish:
    def __init__(
        self,
        message: Message,
        info: UsersUserFull | None,
        pool,
        banners,
        textmap,
        weapon_excel_data,
        avatar_excel_data
    ):
        self.user_id = message.from_id
        self.peer_id = message.peer_id
        self.message = message
        self.info = info
        if info is not None:
            self.full_name = info.first_name + " " + info.last_name
            # Dative (Тимуру Богданову)
            self.full_name_dat = info.first_name_dat + " " + info.last_name_dat
            # Genitive (Тимура Богданова)
            self.full_name_gen = info.first_name_gen + " " + info.last_name_gen
        else:
            self.full_name = "Группа"
            self.full_name_dat = "Группе"
            self.full_name_gen = "Группы"
        self.pool = pool
        self.banners = banners
        self.textmap = textmap
        self.weapon_excel_data = weapon_excel_data
        self.avatar_excel_data = avatar_excel_data
        self.player_gacha_info = []
        self.result_records = []
        self.avatars = []
        self.result_inventory = None
        self.encoder = msgspec.json.Encoder()
        self.decoder = msgspec.json.Decoder()

    async def set_player_info(self):
        logger.info("Setting player gacha info...")
        await self.set_player_gacha_info()
        logger.info("Setting inventory...")
        await self.set_inventory()
        logger.info("Setting records...")
        await self.set_records()
        logger.info("Setting avatars...")
        await self.set_avatars()

    async def update_player_info(self):
        await self.pool.execute(
            "UPDATE players SET gacha_info=$1 ::jsonb, "
            "gacha_records=$2 ::jsonb, "
            "avatars=$3 ::jsonb, "
            "inventory=$4 ::jsonb "
            "WHERE user_id=$5 AND peer_id=$6",
            self.encoder.encode(self.player_gacha_info).decode("utf-8"),
            self.encoder.encode(self.result_records).decode("utf-8"),
            self.encoder.encode(self.avatars).decode("utf-8"),
            self.encoder.encode(self.result_inventory).decode("utf-8"),
            self.user_id,
            self.peer_id
        )

    async def set_player_gacha_info(self):
        gacha_info = await self.pool.fetchrow(
            "SELECT gacha_info FROM players WHERE user_id=$1 AND peer_id=$2",
            self.user_id, self.peer_id
        )
        self.player_gacha_info = self.decoder.decode(gacha_info['gacha_info'].encode("utf-8"))

    async def set_records(self):
        gacha_records = await self.pool.fetchrow(
            "SELECT gacha_records FROM players WHERE user_id=$1 AND peer_id=$2",
            self.user_id, self.peer_id
        )
        self.result_records = self.decoder.decode(gacha_records['gacha_records'].encode("utf-8"))

    async def set_avatars(self):
        avatars = await self.pool.fetchrow(
            "SELECT avatars FROM players WHERE user_id=$1 AND peer_id=$2",
            self.user_id, self.peer_id
        )
        self.avatars = self.decoder.decode(avatars['avatars'].encode("utf-8"))

    async def set_inventory(self):
        inventory = await self.pool.fetchrow(
            "SELECT inventory FROM players WHERE user_id=$1 AND peer_id=$2",
            self.user_id, self.peer_id
        )
        self.result_inventory = self.decoder.decode(inventory['inventory'].encode("utf-8"))

    def get_banner(self, gacha_type: int) -> dict:
        for banner in self.banners:
            if banner['gachaType'] == gacha_type:
                return banner

    def get_banner_player_info(
        self,
        banner_type: Literal[
            "standardBanner", "eventCharacterBanner", "eventWeaponBanner"
        ]
    ):
        for banner in self.player_gacha_info:
            if banner == banner_type:
                return self.player_gacha_info[banner]

    def get_banner_type(self, gacha_type):
        if gacha_type in EVENT_BANNERS:
            return "eventCharacterBanner"
        elif gacha_type in STANDARD_BANNERS:
            return "standardBanner"
        else:
            return "eventWeaponBanner"

    def get_rate_up_items4(self, gacha_type: int) -> tuple:
        banner = self.get_banner(gacha_type)
        rate_up_items4 = banner.get('rateUpItems4')
        return (
            rate_up_items4 if rate_up_items4 is not None else FALLBACK_ITEMS_4_POOL_1
        )

    def get_rate_up_items5(self, gacha_type: int) -> tuple:
        banner = self.get_banner(gacha_type)
        rate_up_items5 = banner.get('rateUpItems5')
        return (
            rate_up_items5 if rate_up_items5 is not None else FALLBACK_ITEMS_5_POOL_1
        )

    def get_fallback_items_4_pool_1(self, gacha_type: int) -> tuple:
        banner = self.get_banner(gacha_type)
        fallback = banner.get('fallbackItems4Pool1')
        return (
            fallback if fallback is not None else FALLBACK_ITEMS_4_POOL_1
        )

    def get_fallback_items_4_pool_2(self, gacha_type: int) -> tuple:
        banner = self.get_banner(gacha_type)
        fallback = banner.get('fallbackItems4Pool2')
        return (
            fallback if fallback is not None else FALLBACK_ITEMS_4_POOL_2
        )

    def get_fallback_items_5_pool_1(self, gacha_type: int) -> tuple:
        banner = self.get_banner(gacha_type)
        fallback = banner.get('fallbackItems5Pool1')
        return (
            fallback if fallback is not None else FALLBACK_ITEMS_5_POOL_1
        )

    def get_fallback_items_5_pool_2(self, gacha_type: int) -> tuple:
        if self.get_banner_type(gacha_type) == 'eventCharacterBanner':
            return []
        banner = self.get_banner(gacha_type)
        fallback = banner.get('fallbackItems5Pool2')
        return (
            fallback if fallback is not None else FALLBACK_ITEMS_5_POOL_2
        )

    def get_failed_featured_item_pulls(self, banner_type: int, rarity):
        match rarity:
            case 4: coinflip_name = "failedFeatured4ItemPulls"
            case _: coinflip_name = "failedFeaturedItemPulls"

        banner = self.get_banner_player_info(banner_type)

        return banner[coinflip_name]

    def set_failed_featured_item_pulls(self, banner_type: int, rarity, count: int):
        match rarity:
            case 4: coinflip_name = "failedFeatured4ItemPulls"
            case _: coinflip_name = "failedFeaturedItemPulls"

        for banner in self.player_gacha_info:
            if banner == banner_type:
                self.player_gacha_info[banner][coinflip_name] == count
                break

    def lerp(self, x, xy_array):
        try:
            if x <= xy_array[0][0]:  # Clamp to first point
                return xy_array[0][1]
            elif x >= xy_array[len(xy_array)-1][0]:  # Clamp to last point
                return xy_array[len(xy_array)-1][1]

            # At this point we're guaranteed to have two lerp
            # points, and pity be somewhere between them.
            for i in range(len(xy_array)-1):
                if x == xy_array[i+1][0]:
                    return xy_array[i+1][1]

                if x < xy_array[i+1][0]:
                    # We are between [i] and [i+1], interpolation time!
                    # Using floats would be slightly cleaner but we can just as
                    # easily use ints if we're careful with order of operations.
                    position = x - xy_array[i][0]
                    full_dist = xy_array[i+1][0] - xy_array[i][0]
                    prev_value = xy_array[i][1]
                    full_delta = xy_array[i+1][1] - prev_value
                    return prev_value + ((position * full_delta) / full_dist)

        except IndexError:
            raise IndexError(
                "Malformed lerp point array. Must be of form [[x0, y0], ..., [xN, yN]]."
            )

        return 0

    def get_weights(self, gacha_type: int, rarity):
        banner = self.get_banner(gacha_type)
        weights = banner.get(f"weights{rarity}")
        fallback_weights = (WEIGHTS5 if rarity == 5 else WEIGHTS4)

        weights = (fallback_weights if weights is None else weights)
        return weights

    def get_weight(self, gacha_type, rarity, pity):
        match rarity:
            case 4:
                weights = self.get_weights(gacha_type, 4)
                return self.lerp(pity, weights)
            case _:
                weights = self.get_weights(gacha_type, 5)
                return self.lerp(pity, weights)

    def get_pool_balance_weight(self, rarity, pity):
        match rarity:
            case 4: return self.lerp(pity, POOL_BALANCE_WEIGHTS4)
            case _: return self.lerp(pity, POOL_BALANCE_WEIGHTS5)

    def get_pity5(self, banner_type) -> int:
        banner = self.get_banner_player_info(banner_type)
        return banner['pity5']

    def get_pity4(self, banner_type) -> int:
        banner = self.get_banner_player_info(banner_type)
        return banner['pity4']

    def get_pity_pool(self, banner_type, rarity, pool):
        banner = self.get_banner_player_info(banner_type)
        match rarity:
            case 4:
                match pool:
                    case 1: return banner['pity4Pool1']
                    case _: return banner['pity4Pool2']
            case _:
                match pool:
                    case 1: return banner['pity5Pool1']
                    case _: return banner['pity5Pool2']

    def get_cost_item(self, gacha_type) -> int:
        return self.get_banner(gacha_type)['costItemId']

    def get_item_count(self, item_id) -> int:
        for item in self.result_inventory:
            if item['id'] == item_id:
                return item['count']

        return 0

    def get_item_rarity(self, item_const, item_id) -> int:
        if item_const >= -1:
            item_id += 9999000
            for avatar in self.avatar_excel_data:
                if avatar['id'] == item_id:
                    return color_to_rarity(avatar['qualityType'])
        else:
            for weapon in self.weapon_excel_data:
                if weapon['id'] == item_id:
                    return weapon['rankLevel']
        logger.warning(f"Unknow item type, item_type is {item_const}, id {item_id}")

    def add_to_records(self, gacha_type, item_type, item_id: int):
        """
        Adds item to local records
        """
        new_item = {
            "gacha_type": gacha_type,
            "item_type": item_type,
            "item_id": item_id,
            "time": int(time.time())
        }

        self.result_records.append(new_item)

    def add_pity5(self, banner_type, amount):
        for banner in self.player_gacha_info:
            if banner == banner_type:
                self.player_gacha_info[banner]['pity5'] += amount
                break

    def add_pity4(self, banner_type, amount):
        for banner in self.player_gacha_info:
            if banner == banner_type:
                self.player_gacha_info[banner]['pity4'] += amount
                break

    def set_pity_pool(self, banner_type, rarity, pool, amount):
        for banner in self.player_gacha_info:
            if banner == banner_type:
                match rarity:
                    case 4:
                        match pool:
                            case 1: self.player_gacha_info[banner]['pity4Pool1'] = amount
                            case _: self.player_gacha_info[banner]['pity4Pool2'] = amount
                    case _:
                        match pool:
                            case 1: self.player_gacha_info[banner]['pity5Pool1'] = amount
                            case _: self.player_gacha_info[banner]['pity5Pool2'] = amount
                break

    def check_avatar_constellation_level(self, item_id: int) -> int:
        if item_id >= 11101 and item_id <= 15511:
            # Weapon
            return -2

        if item_id >= 10000000 and item_id <= 11000100:
            item_id = item_id-9999000

        if item_id >= 1002 and item_id <= 1100:
            # Avatar
            for item in self.avatars:
                if item['id'] == item_id:
                    return item['const']
            # New avatar
            return -1
        if item_id >= 101 and item_id <= 917:
            # Spendable item
            return -3

    def inc_pity_all(self, banner_type):
        for banner in self.player_gacha_info:
            if banner == banner_type:
                self.player_gacha_info[banner]['pity5'] += 1
                self.player_gacha_info[banner]['pity4'] += 1
                break

    def zero_pity(self, banner_type, rarity):
        for banner in self.player_gacha_info:
            if banner == banner_type:
                self.player_gacha_info[banner][f'pity{rarity}'] = 0
                break

    def inc_rolls_stats(self, banner_type, count):
        logger.info(f"Increasing rolls stats for banner {banner_type} {count} times")
        for banner in self.player_gacha_info:
            if banner == banner_type:
                self.player_gacha_info[banner]['totalPulls'] += count
                break

    def add_item(self, item_id, count=1):
        item_const = self.check_avatar_constellation_level(item_id)
        item_exists = False
        if item_const == -3 or item_const == -2:
            for item in self.result_inventory:
                if item['id'] == item_id:
                    item_exists = True
                    item['count'] += count
                    break
            if item_exists is False:
                new_inventory = give_item_local(self.result_inventory, item_id, count)
                self.result_inventory = new_inventory
        elif item_const == -1:
            # New avatar
            new_avatars = give_avatar(self.avatars, item_id)
            self.avatars = new_avatars
        elif item_const >= 0:
            for avatar in self.avatars:
                if avatar['id'] == item_id:
                    avatar['const'] += count
        else:
            raise ValueError(f"Unknown item (returned const: {item_const})")

    def choose_gif(self, rarity: int, ten=False):
        match rarity:
            case 3:
                match ten:
                    case True:
                        raise ValueError("В 10 крутках не найдено ни одного 4* предмета")
                return THREE_STAR
            case 4:
                match ten:
                    case True:
                        return FOUR_STAR_TEN
                    case False:
                        return FOUR_STAR
            case 5:
                match ten:
                    case True:
                        return FIVE_STAR_TEN
                    case False:
                        return FIVE_STAR
            case _:
                raise ValueError(f"Выпал {rarity}* предмет, такого быть не может")

    def draw_roulette(self, weights: list, cutoff) -> bool:
        total = 0
        for weight in weights:
            if weight < 0:
                raise ValueError("Weights must be non-negative!")
            total += weight

        # In grasscutter it's ThreadLocalRandom.current().nextInt((total < cutoff)? total : cutoff);
        # Which return value from 0 to total or cutoff -1,
        # and that's why there is -1 in the end
        roll = random.randint(0, int((total if total < cutoff else cutoff))-1)
        sub_total = 0

        for i in range(len(weights)):
            sub_total += weights[i]
            if roll < sub_total:
                return i

        return 0  # This should only be reachable if total==0

    def do_fallback_rare_pull(self, gacha_type, fallback1, fallback2, rarity):
        banner_type = self.get_banner_type(gacha_type)
        if len(fallback1) < 1:
            if len(fallback2) < 1:
                return random.choice(
                    (FALLBACK_ITEMS_5_POOL_2 if rarity == 5 else FALLBACK_ITEMS_4_POOL_2)
                )
            else:
                return random.choice(fallback2)
        elif len(fallback2) < 1:
            return random.choice(fallback1)
        else:  # Both pools are possible, use the pool balancer
            pity_pool_1 = self.get_pool_balance_weight(
                rarity, self.get_pity_pool(banner_type, rarity, 1)
            )
            pity_pool_2 = self.get_pool_balance_weight(
                rarity, self.get_pity_pool(banner_type, rarity, 2)
            )
            # Larger weight must come first for the
            # hard cutoff to function correctly
            match (1 if pity_pool_1 >= pity_pool_2 else 0):
                case 1: chosen_pool = 1 + self.draw_roulette([pity_pool_1, pity_pool_2], 10000)
                case _: chosen_pool = 2 - self.draw_roulette([pity_pool_2, pity_pool_1], 10000)

            match chosen_pool:
                case 1:
                    self.set_pity_pool(banner_type, rarity, 1, 0)
                    return random.choice(fallback1)
                case _:
                    self.set_pity_pool(banner_type, rarity, 1, 0)
                    return random.choice(fallback2)

    def do_rare_pull(self, gacha_type, rarity, featured, fallback1, fallback2):
        item_id = 0
        banner_type = self.get_banner_type(gacha_type)
        # TODO: Epitomized path
        pity_featured = self.get_failed_featured_item_pulls(banner_type, rarity)
        roll_featured = random.randint(1, 100) <= 50  # 50% chance
        pull_featured = pity_featured or roll_featured

        if pull_featured and len(featured) > 0:
            self.set_failed_featured_item_pulls(banner_type, rarity, False)
            item_id = random.choice(featured)
        else:
            self.set_failed_featured_item_pulls(banner_type, rarity, True)
            item_id = self.do_fallback_rare_pull(gacha_type, fallback1, fallback2, rarity)

        return item_id

    def do_pull(
        self,
        gacha_type,
        pools
    ) -> int:
        banner_type = self.get_banner_type(gacha_type)
        self.inc_pity_all(banner_type)

        weights = (
            self.get_weight(gacha_type, 5, self.get_pity5(banner_type)),
            self.get_weight(gacha_type, 4, self.get_pity4(banner_type)),
            10000
        )
        level_won = 5 - self.draw_roulette(weights, 10000)

        match level_won:
            case 5:
                self.zero_pity(banner_type, 5)
                item_id = self.do_rare_pull(
                    gacha_type,
                    5,
                    pools['rate_up_items_5'],
                    pools['fallback_items_5_pool_1'],
                    pools['fallback_items_5_pool_2']
                )
            case 4:
                self.zero_pity(banner_type, 4)
                item_id = self.do_rare_pull(
                    gacha_type,
                    4,
                    pools['rate_up_items_4'],
                    pools['fallback_items_4_pool_1'],
                    pools['fallback_items_4_pool_2']
                )
            case _:
                item_id = random.choice(FALLBACK_ITEMS_3)

        return item_id

    async def do_pulls(
        self,
        gacha_type,
        times=1
    ):
        banner_type = self.get_banner_type(gacha_type)
        self.inc_rolls_stats(banner_type, times)

        # Sanity check
        if times != 10 and times != 1:
            raise ValueError(f"Player may only wish 1 or 10 times (got {times})")

        # Get banner
        banner = self.get_banner(gacha_type)
        if banner is None:
            raise ValueError(f"Could not get banner with gacha type {gacha_type}")

        # Spend currency
        pay_item = self.get_cost_item(gacha_type)
        if self.get_item_count(pay_item) > 0:
            give_item_local(self.result_inventory, pay_item, -times)
        else:
            match pay_item:
                case 224:
                    cost_item_not_enough = "У вас не достаточно стандартных молитв!"
                    how_to_buy = "стандарт"
                case _:
                    cost_item_not_enough = "У вас не достаточно ивентовых молитв!"
                    how_to_buy = "ивент"
            await self.message.answer(
                cost_item_not_enough
                + f'Купить их можно с помощью команды "!купить молитвы {how_to_buy} <число>"!'
            )
            return

        stardust = 0
        starglitter = 0
        add_stardust = 0
        add_starglitter = 0

        # Generate pools
        pools = {
            'rate_up_items_5': self.get_rate_up_items5(gacha_type),
            'rate_up_items_4': self.get_rate_up_items4(gacha_type),
            'fallback_items_4_pool_1': self.get_fallback_items_4_pool_1(gacha_type),
            'fallback_items_4_pool_2': self.get_fallback_items_4_pool_2(gacha_type),
            'fallback_items_5_pool_1': self.get_fallback_items_5_pool_1(gacha_type),
            'fallback_items_5_pool_2': self.get_fallback_items_5_pool_2(gacha_type)
        }

        max_rarity = 3
        new_items = []

        for _ in range(times):
            # Roll
            new_item = self.do_pull(gacha_type, pools)
            item_data = resolve_id(new_item, self.avatar_excel_data, self.weapon_excel_data)
            if item_data is None:
                raise ValueError(f"New item doesn't exist, returned {new_item}")
            new_items.append(new_item)
            logger.info(new_item)

            # Set item type
            item_const = self.check_avatar_constellation_level(new_item)
            if item_const >= -1:
                item_type = "AVATAR"
            else:
                item_type = "WEAPON"

            # Write gacha record
            self.add_to_records(gacha_type, item_type, new_item)

            add_stardust = 0
            add_starglitter = 0

            # Updating max rarity
            rarity = self.get_item_rarity(item_const, new_item)
            if rarity > max_rarity:
                max_rarity = rarity

            # Const check
            match item_const:
                case -2:  # Weapon
                    match rarity:
                        case 5: add_starglitter = 10
                        case 4: add_starglitter = 2
                        case _: add_stardust = 15
                case _:  # Avatar
                    if item_const >= 6:  # C6
                        add_starglitter = (25 if rarity == 5 else 5)
                    else:  # C0-C5
                        add_starglitter = (10 if rarity == 5 else 2)

            self.add_item(new_item)

            starglitter += add_starglitter
            stardust += add_stardust

        # Adding starglitter and stardust
        if starglitter > 0:
            self.add_item(STARGLITTER_ID, starglitter)
        if stardust > 0:
            self.add_item(STARDUST_ID, stardust)

        logger.info("Updating database player info...")
        await self.update_player_info()

        logger.info("Creating results text...")
        if times == 1:
            results_msg = ""
            item = new_items[0]
            item_info = resolve_id(item, self.avatar_excel_data, self.weapon_excel_data)
            item_name = self.textmap.get(str(item_info['nameTextMapHash']))
            if item_name is None:
                item_name = "Неизвестный предмет"
            item_desc = self.textmap.get(str(item_info['descTextMapHash']))
            if item_desc is None:
                item_desc = "Без описания"
            item_type = self.check_avatar_constellation_level(item_info['id'])

            if item_type >= -1:
                drop_emoji = "&#129485;"
                rarity = color_to_rarity(item_info['qualityType'])
            else:
                drop_emoji = "&#128481;"
                rarity = item_info['rankLevel']

            results_msg = f"{'&#11088;' * rarity} {drop_emoji}: {item_name}\n\"{item_desc}\"\n"
        else:
            if self.info:
                results_msg = f"Результаты [id{self.user_id}|{self.full_name_gen}]:\n"
            else:
                results_msg = f"Результаты {self.full_name_gen}:\n"
            for item in new_items:
                item_info = resolve_id(item, self.avatar_excel_data, self.weapon_excel_data)
                item_name = self.textmap.get(str(item_info['nameTextMapHash']))
                if item_name is None:
                    item_name = "Неизвестный предмет"
                item_type = self.check_avatar_constellation_level(item_info['id'])

                if item_type >= -1:
                    rarity = color_to_rarity(item_info['qualityType'])
                else:
                    rarity = item_info['rankLevel']

                if item_type >= -1:
                    drop_emoji = "&#129485;"
                else:
                    drop_emoji = "&#128481;"

                results_msg += f"{'&#11088;' * rarity} {drop_emoji}: {item_name}\n"

        pity5 = self.get_pity5(banner_type)
        pity4 = self.get_pity4(banner_type)
        banner_name = await get_banner_name(gacha_type)
        results_msg += (
            f"\n&#128160; | Ваш выбранный баннер: {banner_name}\n"
            f"&#128160; | Гарант 5*: {pity5}\n"
            f"&#128160; | Гарант 4*: {pity4}"
        )

        output_gif = self.choose_gif(max_rarity, (True if times == 10 else False))
        if self.info:
            wish_process_text = f"[id{self.user_id}|{self.full_name}] молится..."
        else:
            wish_process_text = f"{self.full_name} молится..."

        # Messages start
        logger.info("Sending wish process text...")
        wish_process_id = await self.message.answer(
            wish_process_text,
            attachment=output_gif,
            disable_mentions=True
        )
        wish_process_id = wish_process_id.conversation_message_id

        await asyncio.sleep(6.0)

        logger.info("Sending wish results text...")
        await bp.api.messages.edit(
            self.peer_id,
            results_msg,
            conversation_message_id=wish_process_id,
            disable_mentions=(True if max_rarity < 5 else False)
        )


async def update_player_banners_info(message: Message):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        player_banners = await pool.fetchrow(
            "SELECT gacha_info FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )
        player_banners = msgspec.json.decode(player_banners['gacha_info'].encode("utf-8"))

        if len(player_banners) == 0:
            player_banners = {
                "standardBanner": {
                    "totalPulls": 0,
                    "pity5": 0,
                    "pity4": 0,
                    "failedFeaturedItemPulls": 0,
                    "failedFeatured4ItemPulls": 0,
                    "pity5Pool1": 0,
                    "pity5Pool2": 0,
                    "pity4Pool1": 0,
                    "pity4Pool2": 0,
                    "failedChosenItemPulls": 0,
                    "wishItemId": 0
                },
                "eventCharacterBanner": {
                    "totalPulls": 0,
                    "pity5": 0,
                    "pity4": 0,
                    "failedFeaturedItemPulls": 0,
                    "failedFeatured4ItemPulls": 0,
                    "pity5Pool1": 0,
                    "pity5Pool2": 0,
                    "pity4Pool1": 0,
                    "pity4Pool2": 0,
                    "failedChosenItemPulls": 0,
                    "wishItemId": 0
                },
                "eventWeaponBanner": {
                    "totalPulls": 0,
                    "pity5": 0,
                    "pity4": 0,
                    "failedFeaturedItemPulls": 0,
                    "failedFeatured4ItemPulls": 0,
                    "pity5Pool1": 0,
                    "pity5Pool2": 0,
                    "pity4Pool1": 0,
                    "pity4Pool2": 0,
                    "failedChosenItemPulls": 0,
                    "wishItemId": 0
                }
            }

        await pool.execute(
            "UPDATE players SET gacha_info=$1 ::jsonb WHERE user_id=$2 AND peer_id=$3",
            msgspec.json.encode(player_banners).decode("utf-8"), message.from_id, message.peer_id
        )


CASES = "first_name_dat, last_name_dat, first_name_gen, last_name_gen"


@bp.on.chat_message(text=(
    '!помолиться <count:int>', '!помолиться',
    '!gjvjkbnmcz <count:int>', '!gjvjkbnmcz',
    '! помолиться <count:int>', '! помолиться',
))
async def use_wish(message: Message, count: int = 1):
    if not await exists(message):
        return
    await update_player_banners_info(message)

    pool = create_pool.pool
    async with pool.acquire() as pool:
        gacha_type = await pool.fetchrow(
            "SELECT current_banner FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )
        gacha_type = gacha_type['current_banner']

        try:
            info = await message.get_user(False, fields=CASES)
        except IndexError:
            # Probably a bot, that generates messages from other people, like @sglypa
            # That's cool! This bot should be able to create a wish
            info = None

        banners = await get_banners()
        textmap = await get_textmap()
        weapon_data = await get_weapon_data()
        avatar_data = await get_avatar_data()
        wish = Wish(
            message, info, pool, banners, textmap, weapon_data, avatar_data
        )
        await wish.set_player_info()

        pay_item = wish.get_cost_item(gacha_type)
        logger.info(f"Banner pay item: {pay_item}")
        if pay_item == 223:  # Event wishes
            fail_text = "ивентовых"
            banner_type = "ивент"
        else:
            fail_text = "стандартных"
            banner_type = "стандарт"

        pay_item_info = await get_item(pay_item, message.from_id, message.peer_id)
        logger.info(f"User has {pay_item_info['count']} of these items")

        if count == 1:
            if pay_item_info['count'] > 0:
                await wish.do_pulls(gacha_type)
                return
        elif count == 10:
            if pay_item_info['count'] >= 10:
                await wish.do_pulls(gacha_type, 10)
                return
        else:
            return "Можно помолиться только 1 или 10 раз!"

        return (
            f"У вас нет {fail_text} круток!\nИх можно купить с "
            f'помощью команды "!купить молитвы {banner_type} <число>"'
        )
