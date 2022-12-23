from . import (
    admin, banners, buy_fates, casino, nickname,
    characters_actions, daily_reward, ping, fun,
    gacha_history, inventory, invite_help, leave,
    minigames, like_reward, print_id, profile, promocodes,
    set_uid, start, top, wish
)

labelers = [
    admin.bl, banners.bl, buy_fates.bl, casino.bl,
    nickname.bl, characters_actions.bl, daily_reward.bl,
    ping.bl, fun.bl, gacha_history.bl, inventory.bl,
    invite_help.bl, leave.bl, minigames.bl, like_reward.bl,
    print_id.bl, profile.bl, promocodes.bl, set_uid.bl, start.bl,
    top.bl, wish.bl
]

__all__ = ["labelers"]

