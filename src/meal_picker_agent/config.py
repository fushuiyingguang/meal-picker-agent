"""全局配置与共享入口。"""

from __future__ import annotations

from pathlib import Path

from .storage import Storage

# 默认地理中心：中原工学院（郑州龙湖校区），演示数据与「定位」均以此为中心
DEFAULT_CENTER = (34.626, 113.705)

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def get_storage() -> Storage:
    """返回已初始化的 Storage 实例（数据库位于项目根 data/）。"""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    storage = Storage(_DATA_DIR / "meal.db")
    storage.init_db()
    return storage
