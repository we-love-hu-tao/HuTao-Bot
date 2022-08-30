from vkbottle.bot import Blueprint, Message
from player_exists import exists
from loguru import logger
from typing import Optional
import time
import drop

bp = Blueprint("Use wish")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(text=("!инвентарь", "!инв", "!инвентарь <rarity>", "!инв <rarity>"))
async def inventory(message: Message, rarity: Optional[str] = None):
    if not await exists(message):
        return
