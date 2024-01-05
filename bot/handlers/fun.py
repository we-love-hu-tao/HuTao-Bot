import random
import re

from vkbottle.bot import BotLabeler, Message

from utils import get_text_map

bl = BotLabeler()
bl.vbml_ignore_case = True


def delete_tags(text_map_string):
    # Remove HTML Tags
    text_map_string = re.sub(r"(<([^>]+)>)", "", text_map_string)

    # Change {NICKNAME} to F1zzTao (my nickname)
    text_map_string = text_map_string.replace(r"{NICKNAME}", "F1zzTao")

    # Replace fake newlines with real newlines
    text_map_string = text_map_string.replace(r"\n", "\n")

    return text_map_string


@bl.message(text=(
    "!рандомная фраза",
    "!<count:int> рандомных фраз",
))
async def generate_random_phrase(message: Message, count=1):
    if count > 10:
        if message.peer_id != message.from_id:
            return "Больше 10 случайных фраз можно искать только в лс!"

    text_map = await get_text_map()
    text_map = list(text_map.values())

    to_send = ""
    i = 0
    while i < count:
        i += 1
        random_line = random.choice(text_map)
        random_line = delete_tags(random_line)
        to_send += f"{random_line}\n\n"

    return to_send


@bl.message(text=(
    "!найти фразу <search_for>",
    "!найти <count:int> фраз <search_for>",
    "!найти <count:int> фразы <search_for>"
))
async def find_phrase(message: Message, search_for, count=1):
    if count > 10:
        if message.peer_id != message.from_id:
            return "Больше 10 фраз можно искать только в лс!"

    text_map = await get_text_map()
    text_map = list(text_map.values())

    search_mode = "s"
    please_wait_id = 0
    if search_for.startswith("r"):
        please_wait_id = await message.answer(
            "Поиск с использованием регулярных выражений может быть долгим, ожидайте..."
        )
        please_wait_id = please_wait_id.conversation_message_id

        search_mode = "r"
        search_for = search_for[1:]

    found_texts = []
    i = 0
    while i < count:
        for text_map_string in text_map:
            found = False
            if search_mode == "r":
                if re.search(search_for, text_map_string):
                    found = True
            else:
                if search_for.lower() in text_map_string.lower():
                    found = True

            if found:
                text_map.remove(text_map_string)
                if search_mode != "r":
                    text_map_string = delete_tags(text_map_string)

                found_texts.append(text_map_string)
                break
        i += 1

    if len(found_texts) <= 0:
        results_text = "Ничего не найдено!"
    else:
        results_text = '\n\n'.join(found_texts)

    if please_wait_id == 0:
        return results_text
    else:
        await message.ctx_api.messages.edit(
            message.peer_id,
            results_text,
            conversation_message_id=please_wait_id
        )
