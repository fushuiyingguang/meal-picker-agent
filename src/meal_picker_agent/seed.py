"""演示数据：中原工学院周边常见美食（含经纬度，围绕中心点 5 公里内分布）。"""

from __future__ import annotations

from .config import DEFAULT_CENTER
from .geo import offset_km
from .models import Dish
from .storage import Storage
from .utils import NEW_CATEGORIES, categorize


def _dish(name: str, category: str, price: float, taste: list[str], meat_type: str,
          km: float, bearing: float) -> Dish:
    """按「中心点 + 距离（公里）+ 方位角」生成菜品，distance 备注存米。"""
    lat, lon = offset_km(DEFAULT_CENTER[0], DEFAULT_CENTER[1], km, bearing)
    return Dish(
        id=None, name=name, category=category, price=price, taste=taste,
        meat_type=meat_type, distance=round(km * 1000), latitude=lat, longitude=lon,
    )


# 16 条预设菜品：分布在以中原工学院（郑州龙湖校区）为中心、半径 5 公里内的不同方位
SEED_DISHES: list[Dish] = [
    _dish("黄焖鸡米饭", "堂食", 22, ["辣", "咸"], "荤", 1.0, 90),        # 东门 1 公里
    _dish("兰州拉面", "面食", 18, ["咸"], "荤", 2.0, 180),               # 南苑 2 公里
    _dish("麻辣烫", "小吃", 25, ["辣", "麻"], "荤", 1.5, 270),           # 西门 1.5 公里
    _dish("沙县蒸饺", "小吃", 12, ["咸"], "荤", 3.0, 0),                 # 北门 3 公里
    _dish("重庆小面", "面食", 15, ["辣", "麻"], "素", 2.5, 135),         # 东南门 2.5 公里
    _dish("皮蛋瘦肉粥", "粥品", 10, ["咸"], "荤", 4.0, 45),              # 东北门 4 公里
    _dish("蔬菜沙拉", "西餐", 20, ["清淡"], "素", 3.5, 225),             # 西南门 3.5 公里
    _dish("汉堡套餐", "外卖", 28, ["咸"], "荤", 1.2, 315),               # 西北门 1.2 公里
    _dish("番茄鸡蛋面", "家常菜", 14, ["清淡", "酸"], "半荤素", 4.5, 60),  # 龙湖广场 4.5 公里
    _dish("宫保鸡丁盖饭", "中餐", 24, ["辣", "咸"], "荤", 2.8, 200),     # 图书馆 2.8 公里
    _dish("扬州炒饭", "中餐", 16, ["咸"], "荤", 3.8, 150),               # 体育馆 3.8 公里
    _dish("凉皮", "小吃", 9, ["酸", "辣"], "素", 0.8, 30),               # 教学楼 0.8 公里
    _dish("烤羊肉串", "烧烤", 30, ["辣", "咸"], "荤", 2.2, 250),         # 学生街 2.2 公里
    _dish("韭菜鸡蛋水饺", "面食", 15, ["咸"], "半荤素", 4.2, 120),       # 美食城 4.2 公里
    _dish("红豆薏米粥", "粥品", 8, ["甜"], "素", 4.8, 210),              # 大学城 4.8 公里
    _dish("提拉米苏", "甜点", 18, ["甜"], "素", 1.8, 100),               # 校医院 1.8 公里
]


def re_categorize_existing(storage: Storage) -> int:
    """用自动分类引擎给现有菜品重新打标：命中关键词且当前为旧分类时覆盖，返回更新条数。"""
    n = 0
    for dish in storage.list_dishes():
        cat = categorize(dish.name)
        if cat and dish.category not in NEW_CATEGORIES:
            storage.update_dish(dish.id, category=cat)
            n += 1
    return n


def seed_demo_data(storage: Storage) -> int:
    """若菜品库为空则导入演示数据；并始终用引擎给现有菜品重新打标，返回导入条数。"""
    seeded = 0
    if not storage.list_dishes():
        for dish in SEED_DISHES:
            storage.add_dish(dish)
        seeded = len(SEED_DISHES)
    re_categorize_existing(storage)
    return seeded
