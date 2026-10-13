"""全局配置与共享入口。"""

from __future__ import annotations

from pathlib import Path

from .storage import Storage

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def get_storage() -> Storage:
    """返回已初始化的 Storage 实例（数据库位于项目根 data/）。"""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    storage = Storage(_DATA_DIR / "meal.db")
    storage.init_db()
    return storage
