import enum
from typing import Optional

import msgspec


class ElemType(enum.Enum):
    ELECT = "Elect"
    FIRE = "Fire"
    GRASS = "Grass"
    ICE = "Ice"
    ROCK = "Rock"
    WATER = "Water"
    WIND = "Wind"


class Avatar(msgspec.Struct):
    """Type that describes avatar from `AvatarData.json`"""
    id: int
    avatar_name: str
    quality: int
    name_text_map_hash: int
    desc_text_map_hash: int
    element: Optional[ElemType] = None
    gacha_img: str = None
