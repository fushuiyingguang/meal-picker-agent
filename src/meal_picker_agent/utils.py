"""自动分类引擎：按菜名关键词自动打上「外卖 / 堂食 / 家常菜」标签。"""

from __future__ import annotations

# 录入界面选「自动分类」视为未手动指定，交给引擎判断
AUTO_CATEGORY = "自动分类"

# 引擎可产出的三个新分类（也用于现有数据重打标时判断是否已处理）
NEW_CATEGORIES = ("外卖", "堂食", "家常菜")

# 无关键词命中且未手动指定时的兜底分类（多数正餐默认堂食）
DEFAULT_CATEGORY = "堂食"

# 关键词按「外卖 → 堂食 → 家常菜」顺序匹配，命中即返回
_WAI_MAI_KEYWORDS = ["汉堡", "炸鸡", "奶茶", "便当", "盖饭", "拌面", "炒面", "炒饭"]
_TANG_SHI_KEYWORDS = ["汤", "粥", "生煎", "包子", "胡辣汤", "现炒", "黄焖鸡"]
_JIA_CHANG_KEYWORDS = ["番茄炒蛋", "红烧", "土豆丝", "青椒肉丝", "家常", "番茄鸡蛋"]


def categorize(name: str) -> str | None:
    """仅按菜名关键词分类，返回「外卖/堂食/家常菜」之一，无命中返回 None。"""
    name = (name or "").strip()
    for kw in _WAI_MAI_KEYWORDS:
        if kw in name:
            return "外卖"
    for kw in _TANG_SHI_KEYWORDS:
        if kw in name:
            return "堂食"
    for kw in _JIA_CHANG_KEYWORDS:
        if kw in name:
            return "家常菜"
    return None


def auto_categorize(name: str, current_category: str | None = None) -> str:
    """录入/导入用自动分类：手动已选分类优先保留，否则按关键词，再否则兜底默认分类。"""
    name = (name or "").strip()
    current = (current_category or "").strip()
    # 用户手动选了具体分类（非空、非「自动分类」）→ 优先保留
    if current and current != AUTO_CATEGORY:
        return current
    return categorize(name) or DEFAULT_CATEGORY


# M2 忌口排除选项：勾选后，菜名或口味字段命中即从候选池剔除
AVOID_OPTIONS = ["辣", "酸", "甜", "香菜", "葱", "蒜", "海鲜", "牛羊肉"]

# 「牛羊肉」展开为「牛 / 羊」：按整词「牛羊肉」几乎匹配不到任何菜名，
# 拆开才能命中「牛肉面 / 羊肉串 / 牛排」等，符合“忌牛羊肉”的语义。
_AVOID_TOKENS = {"牛羊肉": ["牛", "羊"]}


def matches_avoid(name: str, tastes: list[str], avoids: list[str]) -> bool:
    """忌口匹配：任一忌口关键词命中菜名或口味字段即返回 True，用于候选池排他过滤。"""
    if not avoids:
        return False
    haystack = f"{name or ''} " + " ".join(tastes or [])
    for avoid in avoids:
        for token in _AVOID_TOKENS.get(avoid, [avoid]):
            if token in haystack:
                return True
    return False
