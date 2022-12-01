import asyncio
import base64
import io
import random
import time

import msgspec
from loguru import logger
from PIL import Image
from vkbottle import API
from vkbottle.bot import BotLabeler, Message, rules
from vkbottle.http import AiohttpClient
from vkbottle.tools import PhotoMessageUploader

import create_pool
from config import VK_GROUP_TOKEN, GROUP_ID
from utils import exists

bl = BotLabeler()
bl.vbml_ignore_case = True

api = API(VK_GROUP_TOKEN)
photo_upl = PhotoMessageUploader(api)

img_generator = "https://stablehorde.net/api/v2"
http_client = AiohttpClient()

PROMPT_FIRST = "masterpiece, best quality, ((hu tao)), flat chest, black nails, brown hair, long hair, red eyes, (flower-shaped pupils)"
PROMPTS_MAIN = (
    "hat, coat, smile",
    # yes, i love cat girls, questions?
    "cat girl, cat ears, blush",
    "((from behind)), (underwear), black panties, black dress, (clothes lift)",
)
PROMPTS_LAST = (
    # yes, i'm horny, problems?
    "maid",
    "cat girl",
    "dynamic angle",
    "dynamic light",
    "holding cup",
    "holding ice cream",
    "holding food",
    "fire",
)
NEGATIVE_PROMPT = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name"


async def check_token(user_id):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        sh_token = await pool.fetchrow(
            "SELECT sh_token FROM img_gen WHERE user_id=$1",
            user_id
        )
    if sh_token is None:
        return {
            "status": "error",
            "message": "Вы не указали токен от stable horde. Токен можно получить после "
            "создания аккаунта тут: http://stablehorde.net/register\nУказать "
            "токен можно В ЛС ГРУППЫ с помощью команды !shapi <токен>"
        }
    return {
        "status": "success",
        "token": sh_token['sh_token']
    }


async def check_dm_opened(user_id, api):
    can_generate_photo = await api.messages.is_messages_from_group_allowed(
        group_id=GROUP_ID, user_id=user_id
    )
    if can_generate_photo.is_allowed == 0:
        return "Что бы сгенерировать картинку, вам надо дать мне доступ к вашему лс!"
    return True


async def generate_image(prompt: str, sh_token, decoder: msgspec.json.Decoder):
    payload = {
        "prompt": prompt,
        "params": {
            "steps": 30
        },
        "models": ["Anything Diffusion"]
    }
    api_result = None
    generation_uuid = None
    try:
        api_result = decoder.decode(
            await http_client.request_content(
                img_generator+'/generate/async', 'post', json=payload, headers={'apikey': sh_token}
            )
        )
        generation_uuid = api_result['id']
        logger.info(api_result)
    except Exception as e:
        return f"Ошибка при запросе: {e}\n{api_result or 'Апи ничего не вернуло'}"

    finished = False
    while not finished:
        await asyncio.sleep(1.5)
        api_result = decoder.decode(
            await http_client.request_content(
                img_generator+f'/generate/check/{generation_uuid}'
            )
        )
        logger.info(api_result)
        if api_result['done'] and api_result['finished']:
            finished = True

    api_result = decoder.decode(
        await http_client.request_content(
            img_generator+f'/generate/status/{generation_uuid}'
        )
    )
    raw_image = api_result['generations'][0]['img']
    image = Image.open(io.BytesIO(base64.b64decode(raw_image)))
    image_name = f'generated_imgs/{int(time.time())}.png'
    image.save(image_name)
    return {"image": image_name, "api_result": api_result}


@bl.message(text=("!shapi <token>", "!sh api <token>"))
async def set_sh_token(message: Message, token):
    if message.from_id != message.peer_id:
        return (
            "Поздравляю, ты спалил свой токен от stable horde "
            "всем участникам этой беседы, в следующий раз укажи "
            "токен в моем лс"
        )

    if token == '0000000000':
        return "Нельзя использовать анонимный токен!"
 
    try:
        api_result = await http_client.request_json(
            img_generator+'/find_user', headers={'apikey': token}
        )
        if 'message' in api_result:
            return f"Ошибка. Пользователя с этим токеном не существует?\n{api_result}"
    except Exception as e:
        return f"Неизвестная ошибка: {e}"

    pool = create_pool.pool
    async with pool.acquire() as pool:
        await pool.execute(
            "INSERT INTO img_gen (user_id, sh_token) "
            "VALUES ($1, $2) "
            "ON CONFLICT (user_id) DO "
            "UPDATE SET user_id = EXCLUDED.user_id, "
            "sh_token = EXCLUDED.sh_token;",
            message.from_id, token
        )

    return (
        "Вы успешно установили токен от Stable Horde!\n"
        f"Ваш ник: {api_result['username']}"
    )


@bl.message(text=(
    "!ху тао", "!хутао", "!hu tao", "!hutao"
))
async def generate_hu_tao(message: Message):
    if message.from_id == message.peer_id:
        return "Генерировать изображения можно только в чате!"

    if not await exists(message):
        return

    sh_token = await check_token(message.from_id)
    if sh_token['status'] == "error":
        return sh_token['message']
    sh_token = sh_token['token']

    can_generate_photo = await check_dm_opened(message.from_id, message.ctx_api)
    if can_generate_photo is not True:
        return can_generate_photo

    to_edit = (await message.answer("Генерирую Ху Тао...")).conversation_message_id
    start_time = time.time()

    prompt = (
        f'{PROMPT_FIRST}, {random.choice(PROMPTS_MAIN)}, '
        f'{random.choice(PROMPTS_LAST)} ### {NEGATIVE_PROMPT}'
    )

    decoder = msgspec.json.Decoder()
    image = await generate_image(prompt, sh_token, decoder)
    image_name = image['image']
    seed = image['api_result']['generations'][0]['seed']

    # Uploading photo to VK
    photo = await photo_upl.upload(image_name, peer_id=message.from_id)

    end_time = time.time()
    result = (
        f"Сгенерировано за {round(end_time-start_time, 2)}\n"
        f"Промпт: {prompt.split(' ###')[0]}\n"
        f"Сид: {seed}"
    )
    await api.messages.edit(
        message.peer_id,
        result,
        conversation_message_id=to_edit,
        attachment=photo
    )


@bl.message(text=("!prompt <prompt>", "!промпт <prompt>"))
async def generate_by_prompt(message: Message, prompt):
    if message.from_id == message.peer_id:
        return "Генерировать изображения можно только в чате!"

    if not await exists(message):
        return

    sh_token = await check_token(message.from_id)
    if sh_token['status'] == "error":
        return sh_token['message']
    sh_token = sh_token['token']

    can_generate_photo = await check_dm_opened(message.from_id, message.ctx_api)
    if can_generate_photo is not True:
        return can_generate_photo

    to_edit = (await message.answer("Генерирую картинку...")).conversation_message_id
    start_time = time.time()

    decoder = msgspec.json.Decoder() 
    image = await generate_image(prompt, sh_token, decoder)
    image_name = image['image']
    seed = image['api_result']['generations'][0]['seed']
    kudos = image['api_result']['kudos']

    # Uploading photo to VK
    photo = await photo_upl.upload(image_name, peer_id=message.from_id)

    end_time = time.time()
    result = (
        f"Сгенерировано за {round(end_time-start_time, 2)}\n"
        f"Промпт: {prompt.split(' ###')[0]}\n"
        f"Сид: {seed}\n"
        f"Кудосы: {kudos}"
    )
    await api.messages.edit(
        message.peer_id,
        result,
        conversation_message_id=to_edit,
        attachment=photo
    )

