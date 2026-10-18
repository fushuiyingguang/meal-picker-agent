"""数据模型定义。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Dish:
    """菜品。"""

    id: int | None
    name: str
    category: str
    price: float | None = None
    taste: list[str] = field(default_factory=list)  # 口味标签，如 辣/清淡/甜
    meat_type: str = ""                              # 荤素：荤/素/半荤素
    distance: float | None = None                    # 距离（米）
    latitude: float | None = None                    # 纬度
    longitude: float | None = None                   # 经度


@dataclass
class Record:
    """选餐记录；dish_name 为菜名快照，菜品删除后仍可展示。"""

    id: int | None
    dish_id: int | None
    dish_name: str
    selected_at: str
    score: int | None = None
    rating_note: str | None = None
    memo: str = ""                   # 就餐备忘/感受
    source: str = "draw"
