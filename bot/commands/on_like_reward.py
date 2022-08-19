from vkbottle.bot import Blueprint
from vkbottle import GroupEventType, GroupTypes
from loguru import logger
import create_pool


bp = Blueprint("On post like primogems reward")


async def choose_by_level(pool, user_id):
    result = pool.fetchrow("SELECT peer_id FROM players WHERE user_id=$1 ORDER BY exp DESC")
    return result.peer_id


@bp.on.raw_event(
    GroupEventType.LIKE_ADD, GroupTypes.LikeAdd
)
async def like_add(event: GroupTypes.LikeAdd):
    if event.object.object_type.value != "post":  # Когда человек лайкает пост, он лайкает пост и
        return                                    # картинку, 2 ивента, это надо отсеивать

    user_id = event.object.liker_id
    pool = create_pool.pool
    async with pool.acquire() as pool:
        result = await pool.fetch("SELECT peer_id FROM players WHERE user_id=$1", user_id)

    logger.debug(f"Like user id: {user_id}")
    logger.debug(result)
