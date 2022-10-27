import enum
from typing import List, Optional

import msgspec


class BannerType(enum.Enum):
    EVENT = "EVENT"
    WEAPON = "WEAPON"
    STANDARD = "STANDARD"


class Banner(msgspec.Struct, rename="camel"):
    """Type that describes banner from `Banners.json`"""
    gacha_type: int
    schedule_id: int
    banner_type: BannerType
    prefab_path: str
    title_path: str
    cost_item_id: int
    begin_time: int
    end_time: int
    sort_id: int
    rate_up_items_4: Optional[List[int]] = []
    rate_up_items_5: Optional[List[int]] = []
    fallback_items_4_pool_1: Optional[List[int]] = []
    fallback_items_4_pool_2: Optional[List[int]] = []
    fallback_items_5_pool_1: Optional[List[int]] = []
    fallback_items_5_pool_2: Optional[List[int]] = []
    weights_4: Optional[List[List[int]]] = []
    weights_5: Optional[List[List[int]]] = []
