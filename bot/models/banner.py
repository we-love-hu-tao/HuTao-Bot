import enum
from typing import Optional
import msgspec


class BannerType(enum.Enum):
    EVENT = "EVENT"
    WEAPON = "WEAPON"
    STANDARD = "STANDARD"


class Banner(msgspec.Struct):
    """Type that describes banner from `Banners.json`"""
    gacha_type: int
    banner_type: BannerType
    cost_item_id: int
    name_text_map_hash: int
    prefab_id: str
    rate_up_5: Optional[list[int]] = []
    rate_up_4: Optional[list[int]] = []
    weights_4: Optional[list[list[int]]] = []
    weights_5: Optional[list[list[int]]] = []
