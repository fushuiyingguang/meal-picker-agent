"""演示数据：附近常见美食。"""

from __future__ import annotations

from .models import Dish
from .storage import Storage

SEED_DISHES: list[Dish] = [
    Dish(id=None, name="黄焖鸡米饭", category="快餐", price=22, taste=["辣", "咸"], meat_type="荤", distance=300),
    Dish(id=None, name="兰州拉面", category="面食", price=18, taste=["咸"], meat_type="荤", distance=500),
    Dish(id=None, name="麻辣烫", category="小吃", price=25, taste=["辣", "麻"], meat_type="荤", distance=400),
    Dish(id=None, name="沙县蒸饺", category="小吃", price=12, taste=["咸"], meat_type="荤", distance=350),
    Dish(id=None, name="重庆小面", category="面食", price=15, taste=["辣", "麻"], meat_type="素", distance=600),
    Dish(id=None, name="皮蛋瘦肉粥", category="粥品", price=10, taste=["咸"], meat_type="荤", distance=800),
    Dish(id=None, name="蔬菜沙拉", category="西餐", price=20, taste=["清淡"], meat_type="素", distance=700),
    Dish(id=None, name="汉堡套餐", category="快餐", price=28, taste=["咸"], meat_type="荤", distance=450),
    Dish(id=None, name="番茄鸡蛋面", category="面食", price=14, taste=["清淡", "酸"], meat_type="半荤素", distance=520),
    Dish(id=None, name="宫保鸡丁盖饭", category="中餐", price=24, taste=["辣", "咸"], meat_type="荤", distance=380),
    Dish(id=None, name="扬州炒饭", category="中餐", price=16, taste=["咸"], meat_type="荤", distance=420),
    Dish(id=None, name="凉皮", category="小吃", price=9, taste=["酸", "辣"], meat_type="素", distance=550),
    Dish(id=None, name="烤羊肉串", category="烧烤", price=30, taste=["辣", "咸"], meat_type="荤", distance=900),
    Dish(id=None, name="韭菜鸡蛋水饺", category="面食", price=15, taste=["咸"], meat_type="半荤素", distance=480),
    Dish(id=None, name="红豆薏米粥", category="粥品", price=8, taste=["甜"], meat_type="素", distance=650),
    Dish(id=None, name="提拉米苏", category="甜点", price=18, taste=["甜"], meat_type="素", distance=1000),
]


def seed_demo_data(storage: Storage) -> int:
    """若菜品库为空则导入演示数据，返回导入条数。"""
    if storage.list_dishes():
        return 0
    for dish in SEED_DISHES:
        storage.add_dish(dish)
    return len(SEED_DISHES)
