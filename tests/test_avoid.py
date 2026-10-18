"""M2 忌口排除引擎单测。"""

from meal_picker_agent.utils import AVOID_OPTIONS, matches_avoid


def test_avoid_matches_name():
    """菜名命中忌口即排除。"""
    assert matches_avoid("麻辣烫", [], ["辣"]) is True
    assert matches_avoid("香菜牛肉", [], ["香菜"]) is True


def test_avoid_matches_taste():
    """口味字段命中忌口即排除。"""
    assert matches_avoid("水煮鱼", ["辣", "咸"], ["辣"]) is True
    assert matches_avoid("清炒时蔬", ["清淡"], ["辣"]) is False


def test_avoid_multiple_options():
    """多选忌口任一命中即排除，未命中不排除。"""
    assert matches_avoid("红烧肉", ["甜", "咸"], ["酸", "甜"]) is True
    assert matches_avoid("白灼西兰花", ["清淡"], ["辣", "香菜"]) is False


def test_avoid_niuyangrou_expands():
    """「牛羊肉」展开为 牛/羊：牛肉面、羊肉串均命中，鸡/猪不命中。"""
    assert matches_avoid("牛肉面", [], ["牛羊肉"]) is True
    assert matches_avoid("烤羊肉串", [], ["牛羊肉"]) is True
    assert matches_avoid("宫保鸡丁", ["辣"], ["牛羊肉"]) is False


def test_avoid_empty_noop():
    """未勾选忌口时不排除任何菜。"""
    assert matches_avoid("麻辣烫", ["辣"], []) is False
    assert matches_avoid("麻辣烫", ["辣"], None) is False


def test_avoid_options_complete():
    """选项表完整覆盖需求给定的 8 项。"""
    assert AVOID_OPTIONS == ["辣", "酸", "甜", "香菜", "葱", "蒜", "海鲜", "牛羊肉"]
