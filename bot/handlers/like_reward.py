import random
from time import time

from loguru import logger
from vkbottle import GroupEventType, GroupTypes
from vkbottle.bot import BotLabeler
from vkbottle.user import User

import create_pool
from config import GROUP_ID, VK_USER_TOKEN
from item_names import PRIMOGEM
from utils import get_peer_id_by_exp, give_item, translate

bl = BotLabeler()
user = User(VK_USER_TOKEN)

liked_local = {}


@bl.raw_event(GroupEventType.LIKE_ADD, GroupTypes.LikeAdd)
async def like_add(event: GroupTypes.LikeAdd):
    # When user likes a post, he likes both
    # picture and a post, 2 events
    if event.object.object_type is not None:
        if event.object.object_type.value != "post":
            return

    post_id = event.object.object_id
    user_id = event.object.liker_id
    is_liked_post_id = liked_local.get(post_id)
    if is_liked_post_id is not None and user_id in is_liked_post_id:
        return

    logger.debug(liked_local)
    if len(liked_local) >= 10:
        liked_local.clear()

    if liked_local.get(post_id) is not None:
        liked_local[post_id].add(user_id)
    else:
        liked_local[post_id] = {user_id}

    liked_post = await user.api.wall.get_by_id([f"-{GROUP_ID}_{post_id}"])
    liked_post_time = liked_post[0].date or 0

    if int(time()) - liked_post_time > 86400:  # 86400 - 1 day
        return

    pool = create_pool.pool
    async with pool.acquire() as pool:
        add_to = await get_peer_id_by_exp(user_id)
        if add_to == 0:
            return

        result = await pool.fetchrow(
            "SELECT nickname, liked_posts_ids "
            "FROM players WHERE user_id=$1 AND peer_id=$2",
            user_id, add_to
        )

        if post_id in result['liked_posts_ids']:
            return

        await pool.execute(
            "UPDATE players SET liked_posts_ids=array_append(liked_posts_ids, $1) "
            "WHERE user_id=$2 AND peer_id=$3",
            post_id, user_id, add_to
        )
        await give_item(user_id, add_to, PRIMOGEM, 50)

    mention = f"[id{user_id}|{result['nickname']}]"
    link = f"vk.com/we_love_hu_tao?w=wall-{GROUP_ID}_{post_id}\n"

    if random.random() < 0.005:
        ans_message = await translate("like_reward", "on_like_rare")
    else:
        ans_message = await translate("like_reward", "on_like")

    ans_message = ans_message.format(mention=mention, link=link)

    await event.ctx_api.messages.send(
        peer_id=add_to,
        random_id=0,
        message=ans_message
    )
