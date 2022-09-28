from vkbottle.bot import Blueprint, Message
from utils import get_textmap
import random
import re

bp = Blueprint("Fun commands")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(text=("!рандомная фраза", "!<count:int> рандомных фраз"))
async def generate_random_phrase(message: Message, count=1):
    if count > 10:
        return "Ты что, беседу заспамить решил? Нет, столько нельзя!"
    textmap = await get_textmap()
    textmap = list(textmap.values())

    to_send = ""
    i = 0
    while i < count:
        i += 1
        random_line = random.choice(textmap)

        # Remove HTML Tags
        random_line = re.sub(r"(<([^>]+)>)", "", random_line)

        # Change {NICKNAME} to Timius100 (my nickname)
        random_line = random_line.replace(r"{NICKNAME}", "Timius100")

        # Change fake newlines to real newlines
        random_line = random_line.replace(r"\n", "\n")

        to_send += f"{random_line}\n\n"

    return to_send
