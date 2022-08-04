from vkbottle.bot import Bot
from vkbottle import load_blueprints_from_package
import loguru  # noqa: F401


# ! DO NOT RUN THIS, MOVING TO POSTGRESQL


if __name__ == "__main__":
    token = "vk1.a.iwPPxm779OLeQAU8LuTZbtuLWvN6BvfILWPKdLK-Xu4d6rXPmh-pMexWzl6EKAcDhTs3N91DdE9g3wkc2Gf9Eo-1w1XrctReYMI_R12a8yMR626l1N5d6D-doJPySs2HAHu06d4-CnHFVLfJVlbJiBSP0GXKkPfVtGO3S5cOS6lmvEvsXNE2aN_S219Zt64b"  # noqa: E501
    bot = Bot(token=token)

    for bp in load_blueprints_from_package("commands"):
        bp.load(bot)

    bot.run_forever()
