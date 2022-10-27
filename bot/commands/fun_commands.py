import random
import re

from vkbottle.bot import Blueprint, Message

from utils import get_textmap

bp = Blueprint("Fun commands")
bp.labeler.vbml_ignore_case = True


def delete_tags(textmap_string):
    # Remove HTML Tags
    textmap_string = re.sub(r"(<([^>]+)>)", "", textmap_string)

    # Change {NICKNAME} to Timius100 (my nickname)
    textmap_string = textmap_string.replace(r"{NICKNAME}", "Timius100")

    # Replace fake newlines with real newlines
    textmap_string = textmap_string.replace(r"\n", "\n")

    return textmap_string


@bp.on.chat_message(text=(
    "!рандомная фраза",
    "!<count:int> рандомных фраз",
))
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
        random_line = delete_tags(random_line)
        to_send += f"{random_line}\n\n"

    return to_send


@bp.on.chat_message(text=(
    "!найти фразу <search_for>",
    "!найти <count:int> фраз <search_for>",
    "!найти <count:int> фразы <search_for>"
))
async def find_phrase(message: Message, search_for, count=1):
    if count > 10:
        return "Нельзя искать так много, максимум 10 фраз!"

    textmap = await get_textmap()
    textmap = list(textmap.values())

    found_texts = []
    i = 0
    while i < count:
        for textmap_string in textmap:
            if search_for.lower() in textmap_string.lower():
                found_texts.append(delete_tags(textmap_string))
                textmap.remove(textmap_string)
                break
        i += 1

    if len(found_texts) <= 0:
        return "Ничего не найдено!"
    return '\n\n'.join(found_texts)
