from vkbottle.bot import Blueprint, Message
from vkbottle_types.objects import UsersUserFull
from loguru import logger
from typing import Literal
from variables import (
    EVENT_BANNER,
    THREE_STAR,
    FOUR_STAR,
    FIVE_STAR,
    FOUR_STAR_TEN,
    FIVE_STAR_TEN,
    STANDARD_VARIANTS,
    EVENT_VARIANTS,
)
from player_exists import exists
from utils import give_exp, give_character
import create_pool
import asyncio
import drop
import random
import time

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

    async def check_wishes_count(
        self, banner_type: Literal['standard', 'event'], min_: int = 1
    ) -> bool:
        """
        Проверяет, есть ли у игрока желание
        """
        count = await self.pool.fetchrow(
            f"SELECT {banner_type}_wishes FROM players WHERE user_id=$1 AND peer_id=$2",
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

    async def add_to_history(
        self, banner_type: Literal["standard", "event"], drop_type, drop_id: int
    ):
        """
        Добавляет предмет в историю
        """
        new_drop = {
            "banner_type": banner_type,
            "type": drop_type,
            "item_id": drop_id,
            "time": int(time.time())
        }

        new_drop = str(new_drop).replace("'", '"')

        logger.info(f"Добавление в историю этого дропа: {new_drop}")
        await self.pool.execute(
            f"UPDATE players SET {banner_type}_rolls_history=$1 || {banner_type}_rolls_history "
            "::jsonb WHERE user_id=$2 AND peer_id=$3",
            new_drop, self.user_id, self.peer_id
        )

    async def reset_rolls_count(
        self,
        wish: Literal["standard", "event"] = "standard",
        item_type: Literal["rare", "legendary"] = "rare"
    ):
        """
        Обнуляет гарант
        """
        if wish == "standard":
            if item_type == "rare":
                await self.pool.execute(
                    "UPDATE players SET rolls_standard=0 WHERE "
                    "user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )
            elif item_type == "legendary":
                await self.pool.execute(
                    "UPDATE players SET legendary_rolls_standard=0 WHERE "
                    "user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )
        elif wish == "event":
            if item_type == "rare":
                await self.pool.execute(
                    "UPDATE players SET rolls_event=0 WHERE user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )
            elif item_type == "legendary":
                await self.pool.execute(
                    "UPDATE players SET legendary_rolls_event=0 WHERE "
                    "user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )

    async def decrease_wish(
        self,
        banner_type: Literal["standard", "event"] = "standard",
        count: int = 1
    ):
        await self.pool.execute(
            f"UPDATE players SET {banner_type}_wishes={banner_type}_wishes-$1 WHERE "
            "user_id=$2 AND peer_id=$3",
            count, self.user_id, self.peer_id
        )

    async def increase_rolls_count(
        self,
        wish: Literal["standard", "event"] = "standard",
        item_type: Literal["rare", "legendary", "both"] = "both"
    ):
        """
        Увеличивает гарант
        """
        if wish == "standard":
            if item_type == "rare" or item_type == "both":
                await self.pool.execute(
                    "UPDATE players SET rolls_standard=rolls_standard+1 "
                    "WHERE user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )
            if item_type == "legendary" or item_type == "both":
                await self.pool.execute(
                    "UPDATE players SET "
                    "legendary_rolls_standard=legendary_rolls_standard+1 "
                    "WHERE user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )
        elif wish == "event":
            if item_type == "rare" or item_type == "both":
                await self.pool.execute(
                    "UPDATE players SET rolls_event=rolls_event+1 WHERE "
                    "user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )
            if item_type == "legendary" or item_type == "both":
                await self.pool.execute(
                    "UPDATE players SET "
                    "legendary_rolls_event=legendary_rolls_event+1 WHERE "
                    "user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )

    async def choose_gif(self, rarity: int, ten=False) -> int:
        if rarity == 3:
            # 3 star gif
            msg_id = await self.message.answer(
                f"[id{self.user_id}|{self.full_name}] молится...",
                attachment=THREE_STAR,
                disable_mentions=True
            )
        elif rarity == 4:
            if ten:
                # 4 star gif 10 items
                msg_id = await self.message.answer(
                    f"[id{self.user_id}|{self.full_name}] молится...",
                    attachment=FOUR_STAR_TEN,
                    disable_mentions=True
                )
            else:
                # 4 star gif
                msg_id = await self.message.answer(
                    f"[id{self.user_id}|{self.full_name}] молится...",
                    attachment=FOUR_STAR,
                    disable_mentions=True
                )
        elif rarity >= 5:
            if ten:
                # 5 star gif 10 times
                msg_id = await self.message.answer(
                    f"[id{self.user_id}|{self.full_name}] молится...",
                    attachment=FIVE_STAR_TEN,
                    disable_mentions=True
                )
            else:
                # 5 star gif
                msg_id = await self.message.answer(
                    f"[id{self.user_id}|{self.full_name}] молится...",
                    attachment=FIVE_STAR,
                    disable_mentions=True
                )

        return msg_id.conversation_message_id

    async def roll(self, banner_type: Literal["standard", "event"]) -> tuple:
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
        counter4_standard = count[1]
        counter5_standard = count[2]
        counter4_event = count[3]
        counter5_event = count[4]

        # https://m.hoyolab.com/#/article/497840
        rate5 = 0.006
        rate4 = 0.051
        pity5 = 73
        pity4 = 8

        if banner_type == "standard":
            chance = random.random()
            prob5 = rate5 + max(0, (counter5_standard-pity5) * 10 * rate5)
            prob4 = rate4 + max(0, (counter4_standard-pity4) * 10 * rate4)
            logger.info(
                "Выбор случайного стандартного предмета для "
                f"игрока {self.user_id} в беседе {self.peer_id}"
            )
            logger.info(f"Счетчик 5 звездочного стандартного предмета: {counter5_standard}")
            logger.info(f"Счетчик 4 звездочного стандартного предмета: {counter4_standard}")
            logger.info(f"Шанс на 5 звездочный предмет: {prob5}")
            logger.info(f"Шанс на 4 звездочный предмет: {prob4}")
            if chance < prob5:
                await self.reset_rolls_count(item_type="legendary")
                await self.increase_rolls_count(item_type="rare")
                type_rarity = random.choice(
                    (
                        drop.legendary_standard_characters,
                        drop.legendary_standard_weapons,
                    )
                )
            elif chance < prob4 + prob5:
                await self.reset_rolls_count()
                await self.increase_rolls_count(item_type="legendary")
                type_rarity = random.choice(
                    (
                        drop.rare_standard_characters,
                        drop.rare_standard_weapons,
                    )
                )

            else:
                await self.increase_rolls_count()
                type_rarity = drop.normal_standard_weapons

            random_item = random.choice(list(type_rarity.items())[1:])

            if random_item[1]["type"] == "character":
                await give_character(
                    self.user_id, self.peer_id, type_rarity["_type"], random_item[1]["_id"]
                )
            await self.add_to_history(
                "standard", type_rarity["_type"], random_item[1]["_id"]
            )
            await give_exp(
                random.randint(10, 80), self.user_id, self.peer_id, bp.api
            )
            return random_item

        elif banner_type == "event":
            chance = random.random()
            prob5 = rate5 + max(0, (counter5_event-pity5) * 10 * rate5)
            prob4 = rate4 + max(0, (counter4_event-pity4) * 10 * rate4)
            logger.info(
                "Выбор случайного ивентового предмета для "
                f"игрока {self.user_id} в беседе {self.peer_id}"
            )
            logger.info(f"Счетчик 5 звездочного ивентового предмета: {counter5_event}")
            logger.info(f"Счетчик 4 звездочного ивентового предмета: {counter4_event}")
            logger.info(f"Шанс на 5 звездочный предмет: {prob5}")
            logger.info(f"Шанс на 4 звездочный предмет: {prob4}")

            if chance < prob5:
                # 5 звездочный персонаж
                await self.reset_rolls_count(wish="event", item_type="legendary")
                await self.increase_rolls_count(wish="event", item_type="rare")

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

            elif chance < prob4 + prob5:
                # 4 звездочный персонаж/оружие
                await self.reset_rolls_count(wish="event")
                await self.increase_rolls_count(
                    wish="event", item_type="legendary"
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

            if type_rarity == drop.legendary_standard_characters:
                await self.pool.execute(
                    "UPDATE players SET event_char_guarantee=true "
                    "WHERE user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )

            if type_rarity == drop.legendary_event_characters:
                await self.pool.execute(
                    "UPDATE players SET event_char_guarantee=false "
                    "WHERE user_id=$1 AND peer_id=$2",
                    self.user_id, self.peer_id
                )
                for character in type_rarity.items():
                    if character[0] != "_type":
                        if character[1]["event"] == EVENT_BANNER:
                            random_item = character
            else:
                random_item = random.choice(list(type_rarity.items())[1:])

            if random_item[1]["type"] == "character":
                await give_character(
                    self.user_id, self.peer_id, type_rarity["_type"], random_item[1]["_id"]
                )

            await self.add_to_history(
                "event", type_rarity["_type"], random_item[1]["_id"]
            )
            await give_exp(
                random.randint(50, 120), self.user_id, self.peer_id, bp.api
            )
            return random_item

    async def use_wish(self, roll_type):
        """
        Использует молитву
        """
        await self.decrease_wish(roll_type, 1)

        item_drop = await self.roll(roll_type)
        item_type = item_drop[1]["type"]
        item_rarity = item_drop[1]["rarity"]
        name = item_drop[0]
        picture = item_drop[1]["picture"]

        edit_msg_id = await self.choose_gif(item_rarity)
        await asyncio.sleep(6.0)

        if item_type == "weapon":
            await bp.api.messages.edit(
                self.peer_id,
                f"[id{self.user_id}|{self.full_name_dat}] выпало оружие "
                f"{name} {'&#11088;' * item_rarity}!",
                conversation_message_id=edit_msg_id,
                attachment=picture,
                disable_mentions=(True if item_rarity < 4 else False)
            )
        elif item_type == "character":
            await bp.api.messages.edit(
                self.peer_id,
                f"[id{self.user_id}|{self.full_name_dat}] выпал персонаж "
                f"{name} {'&#11088;' * item_rarity}!",
                conversation_message_id=edit_msg_id,
                attachment=picture,
                disable_mentions=(True if item_rarity < 4 else False)
            )

    async def use_ten_wishes(self, roll_type: Literal["standard", "event"]):
        """
        Использует 10 молитв
        """
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
                    f"{'&#11088;' * item_rarity} &#128481;: {item_name}\n"
                )
            elif item_type == "character":
                output += (
                    f"{'&#11088;' * item_rarity} &#129485;: {item_name}\n"
                )

        if five_star:
            edit_msg_id = await self.choose_gif(5, True)
        else:
            edit_msg_id = await self.choose_gif(4, True)

        await asyncio.sleep(6.1)
        await bp.api.messages.edit(
            self.peer_id,
            output,
            conversation_message_id=edit_msg_id,
            disable_mentions=(True if item_rarity < 5 else False)
        )


CASES = "first_name_dat, last_name_dat, first_name_gen, last_name_gen"


@bp.on.chat_message(text=('!помолиться <banner_type> 10', '!помолиться <banner_type>'))
async def use_a_wish(message: Message, banner_type):
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        fail_text = None
        if banner_type in STANDARD_VARIANTS:
            banner_type = "standard"
            fail_text = "стандартных"
        elif banner_type in EVENT_VARIANTS:
            banner_type = "event"
            fail_text = "ивентовых"
        else:
            return f"{banner_type} молитв не существует, уебище, ливни с позором нахуй (!удалить геншин)!"

        info = await message.get_user(False, fields=CASES)
        wish = Wish(message, info, pool)

        if message.text.split()[-1] != 10:    # если чел 1 крутит
            if await wish.check_wishes_count(banner_type=banner_type):
                await wish.use_wish(banner_type)
        elif message.text.split()[-1] == 10:  # если чел 10 крутит
            if await wish.check_wishes_count(banner_type=banner_type, min_=10):
                await wish.use_ten_wishes(banner_type)
        else:
            await message.answer(
                f'У вас нет {fail_text} круток!\nИх можно купить с '
                f'помощью команды "!купить молитвы {banner_type} <число>"'
            )
