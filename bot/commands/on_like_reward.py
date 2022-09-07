from vkbottle.bot import Blueprint
from vkbottle.user import User
from vkbottle import GroupEventType, GroupTypes
from loguru import logger
from variables import VK_USER_TOKEN, GROUP_ID
from time import time
import create_pool

# ! NOT IMPLEMENTED

bp = Blueprint("On post like primogems reward")
user = User(VK_USER_TOKEN)


@bp.on.raw_event(GroupEventType.LIKE_ADD, GroupTypes.LikeAdd)
async def like_add(event: GroupTypes.LikeAdd):
    if (
        event.object.object_type.value != "post"
    ):          # Когда человек лайкает пост, он лайкает пост и
        return  # картинку, 2 ивента, это надо отсеивать

    post_id = event.object.object_id
    liked_post = await user.api.wall.get_by_id(f"-{GROUP_ID}_{post_id}")
    liked_post_time = liked_post[0].date

    if int(time()) - liked_post_time > 86400:  # 86400 - 1 день
        return

    user_id = event.object.liker_id
    pool = create_pool.pool
    async with pool.acquire() as pool:
        result = await pool.fetchrow(
            "SELECT liked_posts_ids, experience, peer_id, nickname FROM players WHERE "
            "user_id=$1 ORDER BY experience DESC",
            user_id,
        )
        logger.info(f"Результат выбора: {result}")

        if result is None or len(result) == 0:
            return

        if post_id in result['liked_posts_ids']:
            return

        await pool.execute(
            "UPDATE players SET primogems=primogems+50, "
            "liked_posts_ids=array_append(liked_posts_ids, $1) "
            "WHERE user_id=$2 AND peer_id=$3",
            post_id, user_id, result['peer_id']
        )

    await bp.api.messages.send(
        peer_id=result['peer_id'],
        random_id=0,
        message=(
            f"[id{user_id}|{result['nickname']}], спасибо за лайк на пост "
            f"vk.com/we_love_hu_tao?w=wall-{GROUP_ID}_{post_id}!\n"
            "За это вы получаете 50 примогемов!"
        ),
    )

    logger.info(f"Айди лайкнувшего пост пользователя: {user_id}")
    logger.info(f"Инфо о посте: {liked_post}")
