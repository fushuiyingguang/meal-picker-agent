"""自动分类引擎单测。"""

from meal_picker_agent.utils import auto_categorize, categorize


def test_auto_categorize_huangmenji_rice():
    """「黄焖鸡米饭」应自动归入 外卖 或 堂食。"""
    assert auto_categorize("黄焖鸡米饭", "") in ("外卖", "堂食")


def test_auto_categorize_preserves_manual_category():
    """用户手动选了分类时优先保留。"""
    assert auto_categorize("汉堡套餐", "中餐") == "中餐"
    assert auto_categorize("扬州炒饭", "快餐") == "快餐"


def test_auto_categorize_keywords():
    """关键词规则：外卖 / 堂食 / 家常菜。"""
    assert auto_categorize("汉堡套餐", "") == "外卖"
    assert auto_categorize("扬州炒饭", "") == "外卖"
    assert auto_categorize("皮蛋瘦肉粥", "") == "堂食"
    assert auto_categorize("红烧肉", "") == "家常菜"
    assert auto_categorize("番茄鸡蛋面", "") == "家常菜"


def test_categorize_returns_none_without_keyword():
    """无关键词命中时 categorize 返回 None（由调用方决定兜底）。"""
    assert categorize("兰州拉面") is None
    assert categorize("提拉米苏") is None
