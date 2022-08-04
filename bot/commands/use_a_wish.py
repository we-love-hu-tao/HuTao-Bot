from vkbottle.bot import Blueprint, Message
from vkbottle_types.objects import UsersUserFull
from player_exists import exists
from variables import (
    EVENT_BANNER,
    THREE_STAR,
    FOUR_STAR,
    FIVE_STAR,
    FOUR_STAR_TEN,
    FIVE_STAR_TEN,
)
import asyncpg
import asyncio
import drop
import random

bp = Blueprint("Use wish")
bp.labeler.vbml_ignore_case = True


class Wish:
    def __init__(self, message: Message, info: UsersUserFull, pool):
        self.user_id = message.from_id
        self.peer_id = message.peer_id
        self.message = message
        self.full_name = info.first_name + " " + info.last_name
        # Дательный падеж (Тимуру Богданову)
        self.full_name_dat = info.first_name_dat + " " + info.last_name_dat
        # Родительный падеж (Тимура Богданова)
        self.full_name_gen = info.first_name_gen + " " + info.last_name_gen
        self.pool = pool

    async def check_standard(self, min_=1) -> bool:
        """
        Проверяет, есть ли у игрока стандартное желание
        """
        count = await self.pool.fetchrow(
            "SELECT standard_wishes FROM players WHERE user_id=$1 AND peer_id=$2",
            self.user_id, self.peer_id
        )
        if count[0] >= min_:
            return True
        return False

    async def check_event(self, min_=1) -> bool:
        """
        Проверяет, есть ли у игрока ивентовое желание
        """
        count = await self.pool.fetchrow(
            "SELECT event_wishes FROM players WHERE user_id=$1 AND peer_id=$2",
            self.user_id, self.peer_id
        )
        if count[0] >= min_:
            return True
        return False

    def chance(self, num: float) -> bool:
        """
        Возвращает шанс
        >>> chance(50.0)
        >>> True
        """
        return True if random.random() * 100 < num else False

    async def reset_rolls_count(self, wish="standard", type_="rare"):
        """
        Обнуляет гарант
        """
        if wish == "standard":
            if type_ == "rare":
                await self.pool.execute(
                    "UPDATE players SET rolls_standard=0 WHERE "
                    "user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )
            elif type_ == "legendary":
                await self.pool.execute(
                    "UPDATE players SET legendary_rolls_standard=0 WHERE "
                    "user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )
        elif wish == "event":
            if type_ == "rare":
                await self.pool.execute(
                    "UPDATE players SET rolls_event=0 WHERE user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )
            elif type_ == "legendary":
                await self.pool.execute(
                    "UPDATE players SET legendary_rolls_event=0 WHERE "
                    "user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )

    async def decrease_wish(self, type_="standard", count=1):
        if type_ == "standard":
            await self.pool.execute(
                "UPDATE players SET standard_wishes=standard_wishes-$1 WHERE "
                "user_id=$2 AND peer_id=$3",
                count, self.user_id, self.peer_id
            )
        elif type_ == "event":
            await self.pool.execute(
                "UPDATE players SET event_wishes=event_wishes-$1 WHERE "
                "user_id=$2 AND peer_id=$3",
                count, self.user_id, self.peer_id
            )

    async def increase_rolls_count(self, wish="standard", type_="both"):
        """
        Увеличивает гарант
        """
        if wish == "standard":
            if type_ == "rare" or type_ == "both":
                await self.pool.execute(
                    "UPDATE players SET rolls_standard=rolls_standard+1"
                    " WHERE user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )
            if type_ == "legendary" or type_ == "both":
                await self.pool.execute(
                    "UPDATE players SET "
                    "legendary_rolls_standard=legendary_rolls_standard+1 "
                    "WHERE user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )
        elif wish == "event":
            if type_ == "rare" or type_ == "both":
                await self.pool.execute(
                    "UPDATE players SET rolls_event=rolls_event+1 WHERE "
                    "user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )
            if type_ == "legendary" or type_ == "both":
                await self.pool.execute(
                    "UPDATE players SET "
                    "legendary_rolls_event=legendary_rolls_event+1 WHERE "
                    "user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )

    async def choose_gif(self, rarity, ten=False):
        if rarity == 3:
            # 3 star gif
            await self.message.answer(
                f"[id{self.user_id}|{self.full_name}] молится...",
                attachment=THREE_STAR,
                disable_mentions=True
            )
        elif rarity == 4:
            if ten:
                # 4 star gif 10 items
                await self.message.answer(
                    f"[id{self.user_id}|{self.full_name}] молится...",
                    attachment=FOUR_STAR_TEN,
                    disable_mentions=True
                )
            else:
                # 4 star gif
                await self.message.answer(
                    f"[id{self.user_id}|{self.full_name}] молится...",
                    attachment=FOUR_STAR,
                    disable_mentions=True
                )
        elif rarity == 5:
            if ten:
                # 5 star gif 10 times
                await self.message.answer(
                    f"[id{self.user_id}|{self.full_name}] молится...",
                    attachment=FIVE_STAR_TEN,
                    disable_mentions=True
                )
            else:
                # 5 star gif
                await self.message.answer(
                    f"[id{self.user_id}|{self.full_name}] молится...",
                    attachment=FIVE_STAR,
                    disable_mentions=True
                )

    async def roll(self, type) -> tuple:
        count = await self.pool.fetchrow(
            """
            SELECT
            event_char_guarantee,
            rolls_standard,
            legendary_rolls_standard,
            rolls_event,
            legendary_rolls_event
            FROM players WHERE user_id=$1 AND peer_id=$2
            """,
            self.user_id, self.peer_id
        )
        event_char_guarantee = count[0]
        rolls_standard_count = count[1]
        legendary_rolls_standard_count = count[2]
        rolls_event_count = count[3]
        legendary_rolls_event_count = count[4]

        if type == "standard":
            # Если игрок достиг гаранта, то ему выпадает 5 звездочный предмет.
            # В ином случае если игрок достиг 70 крутки,
            # его шанс увеличивается на 20%.
            if legendary_rolls_standard_count >= 89:
                drop_chance = 100.0
            elif legendary_rolls_standard_count >= 70:
                drop_chance = 5.0
            else:
                drop_chance = 1.6
            if self.chance(drop_chance):
                await self.reset_rolls_count(type_="legendary")
                await self.increase_rolls_count(type_="rare")
                type_rarity = random.choice(
                    (
                        drop.legendary_standard_characters,
                        drop.legendary_standard_weapons,
                    )
                )
            elif self.chance(13.0) or rolls_standard_count >= 9:
                await self.reset_rolls_count()
                await self.increase_rolls_count(type_="legendary")
                type_rarity = random.choice(
                    (
                        drop.rare_standard_characters,
                        drop.rare_standard_weapons,
                    )
                )

            else:
                await self.increase_rolls_count()
                type_rarity = drop.normal_standard_weapons

            random_item = random.choice(list(type_rarity.items()))
            return random_item

        elif type == "event":
            if legendary_rolls_event_count >= 89:    # Гарант на 5* персонажа
                drop_chance = 100.0
            elif legendary_rolls_event_count >= 70:  # Софт-гарант
                drop_chance = 5.0
            else:
                drop_chance = 1.6
            if self.chance(drop_chance):
                # 5 звездочный персонаж
                await self.reset_rolls_count(wish="event", type_="legendary")
                await self.increase_rolls_count(wish="event", type_="rare")

                # Если игроку раннее выпал стандартный персонаж в ивент
                # баннере, он точно получит персонажа из ивент баннера
                if event_char_guarantee:
                    type_rarity = drop.legendary_event_characters
                else:
                    type_rarity = random.choice(
                        (
                            drop.legendary_event_characters,
                            drop.legendary_standard_characters,
                        )
                    )

            elif self.chance(13.0) or rolls_event_count >= 9:
                # 4 звездочный персонаж/оружие
                await self.reset_rolls_count(wish="event")
                await self.increase_rolls_count(
                    wish="event", type_="legendary"
                )
                type_rarity = random.choice(
                    (
                        drop.rare_standard_characters,
                        drop.rare_standard_weapons,
                    )
                )
            else:
                # Стандартное оружие
                # Увеличение числа для получения гаранта
                await self.increase_rolls_count("event")
                type_rarity = drop.normal_standard_weapons
            if type_rarity == drop.legendary_event_characters:
                for character in type_rarity.items():
                    if character[1]["event"] == EVENT_BANNER:
                        return character
            else:
                return random.choice(list(type_rarity.items()))

    async def use_wish(self, type):
        """
        Использует молитву
        """
        await self.decrease_wish(type, 1)
        item_drop = await self.roll(type)
        type = item_drop[1]["type"]
        rarity = item_drop[1]["rarity"]
        name = item_drop[0]
        picture = item_drop[1]["picture"]

        await self.choose_gif(rarity)
        await asyncio.sleep(6.0)
        if type == "weapon":
            await self.message.answer(
                f"[id{self.user_id}|{self.full_name_dat}] выпало оружие "
                f"{name} ({'★' * rarity})!",
                attachment=picture,
                disable_mentions=(True if rarity < 4 else False)
            )
        elif type == "character":
            await self.message.answer(
                f"[id{self.user_id}|{self.full_name_dat}] выпал персонаж "
                f"{name} ({'★' * rarity})!",
                attachment=picture,
                disable_mentions=(True if rarity < 4 else False)
            )

    async def use_ten_wishes(self, roll_type):
        item_drops = []
        output = f"Результаты [id{self.user_id}|{self.full_name_gen}]\n"
        five_star = False
        await self.decrease_wish(roll_type, 10)
        for i in range(0, 10):
            new_drop = await self.roll(roll_type)
            item_drops.append(new_drop)
            item_type = item_drops[i][1]["type"]
            item_rarity = item_drops[i][1]["rarity"]
            if item_rarity == 5:
                five_star = True
            item_name = item_drops[i][0]
            if item_type == "weapon":
                output += (
                    f"Выпало оружие {item_name} ({'★' * item_rarity})!\n"
                )
            elif item_type == "character":
                output += (
                    f"Выпал персонаж {item_name} ({'★' * item_rarity})!\n"
                )
        if five_star:
            await self.choose_gif(5, True)
        else:
            await self.choose_gif(4, True)
        await asyncio.sleep(6.0)
        await self.message.answer(output, disable_mentions=True)


CASES = "first_name_dat, last_name_dat, first_name_gen, last_name_gen"


@bp.on.message(text="!помолиться стандарт")
async def standard_wish(message: Message):
    async with asyncpg.create_pool(
        user="postgres", database="genshin_bot", passfile="pgpass.conf"
    ) as pool:
        async with pool.acquire() as db:
            if not await exists(message, db):
                return
            info = await message.get_user(False, fields=CASES)
            wish = Wish(message, info, db)
            if await wish.check_standard():
                await wish.use_wish("standard")
            else:
                await message.answer("У вас нет стандартных круток!")


@bp.on.message(text="!помолиться стандарт 10")  # !
async def ten_standard_wishes(message: Message):
    async with asyncpg.create_pool(
        user="postgres", database="genshin_bot", passfile="pgpass.conf"
    ) as pool:
        async with pool.acquire() as db:
            if not await exists(message, db):
                return
            info = await message.get_user(False, fields=CASES)
            wish = Wish(message, info, db)  # !
            if await wish.check_standard(10):
                await wish.use_ten_wishes("standard")
            else:
                await message.answer("Вам не хватает стандартных круток!")


@bp.on.message(text=("!помолиться событие", "!помолиться ивент"))
async def event_wish(message: Message):
    async with asyncpg.create_pool(
        user="postgres", database="genshin_bot", passfile="pgpass.conf"
    ) as pool:
        async with pool.acquire() as db:
            if not await exists(message, db):
                return
            info = await message.get_user(False, fields=CASES)
            wish = Wish(message, info, db)
            if await wish.check_event():
                await wish.use_wish("event")
            else:
                await message.answer("У вас нет ивентовых круток!")


@bp.on.message(text=("!помолиться событие 10", "!помолиться ивент 10"))
async def ten_event_wishes(message: Message):
    async with asyncpg.create_pool(
        user="postgres", database="genshin_bot", passfile="pgpass.conf"
    ) as pool:
        async with pool.acquire() as db:
            if not await exists(message, db):
                return
            info = await message.get_user(False, fields=CASES)
            wish = Wish(message, info, db)
            if await wish.check_event(10):
                await wish.use_ten_wishes("event")
            else:
                await message.answer("Вам не хватает ивентовых круток!")
