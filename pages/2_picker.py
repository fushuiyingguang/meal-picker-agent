"""M2 智能筛选与摇号：用餐模式 + 就餐人数 + 一桌菜搭配（荤素/分类/总预算）+ 随机摇号。"""

import sys
from pathlib import Path

# 将项目的 src 目录添加到 Python 搜索路径（页面位于 pages/ 子目录，需向上回溯一层）
src_path = Path(__file__).resolve().parents[1] / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import random

import streamlit as st

from meal_picker_agent.config import DEFAULT_CENTER, get_storage
from meal_picker_agent.geo import haversine_km
from meal_picker_agent.seed import seed_demo_data
from meal_picker_agent.utils import AVOID_OPTIONS, matches_avoid

st.set_page_config(page_title="智能筛选与摇号", page_icon="🎲")

CATEGORIES = ["中餐", "快餐", "面食", "小吃", "西餐", "粥品", "甜点", "烧烤", "外卖", "堂食", "家常菜"]
TASTES = ["辣", "麻", "清淡", "甜", "咸", "酸"]

# 早餐品类关键词：聚餐模式下剔除，避免正餐场景抽出纯早餐（单人简餐保留）
BREAKFAST_KEYWORDS = ["包", "粥", "鸡蛋", "油条", "豆浆", "胡辣汤", "馒头", "烧麦", "早餐"]
# 白名单：名字里带这些片段的正餐小吃不判为早餐（如「饼卷青椒鸡蛋」）
BREAKFAST_WHITELIST = ["饼卷"]

# 五种用餐模式预设：就餐人数、总预算区间（元）、距离（公里）、口味、荤素倾向、分类
MODE_NAMES = ["单人简餐", "朋友小聚", "家庭聚餐", "公司聚餐", "社团团建"]
MODES = {
    "单人简餐": {"people": 1, "price": (10, 25), "km": 1.0, "taste": ["清淡", "咸"], "meat_type": "全部", "category": []},
    "朋友小聚": {"people": 3, "price": (20, 60), "km": 3.0, "taste": [], "meat_type": "荤", "category": ["小吃", "烧烤"]},
    "家庭聚餐": {"people": 5, "price": (30, 100), "km": 5.0, "taste": [], "meat_type": "全部", "category": []},
    "公司聚餐": {"people": 8, "price": (50, 150), "km": 5.0, "taste": [], "meat_type": "荤", "category": ["中餐", "快餐"]},
    "社团团建": {"people": 6, "price": (30, 80), "km": 3.0, "taste": [], "meat_type": "全部", "category": ["烧烤", "小吃"]},
}

storage = get_storage()
seed_demo_data(storage)

st.title("🎲 智能筛选与摇号")


def _dish_count(n: int) -> int:
    """就餐人数 → 菜品数量（N+1 / N+2 法则）。"""
    if n <= 1:
        return 1
    if n <= 5:
        return n + 1
    return n + 2


def _meat_ratio(meat_type: str) -> float:
    """荤素倾向 → 荤菜占比（默认 60% 荤 + 40% 素）。"""
    return {"荤": 0.7, "素": 0.4}.get(meat_type, 0.6)


def _is_breakfast(name: str) -> bool:
    """判断菜名是否为纯早餐品类：白名单优先，鸡蛋用精确/结尾匹配避免误伤正餐小吃。"""
    if any(w in name for w in BREAKFAST_WHITELIST):
        return False
    for kw in BREAKFAST_KEYWORDS:
        if kw == "鸡蛋":
            if name == "鸡蛋" or name.endswith("鸡蛋"):
                return True
        elif kw in name:
            return True
    return False


def _spread_sample(pool, n):
    """从 pool 中抽 n 个，尽量覆盖不同 category，避免全落同一个分类。"""
    if n <= 0 or not pool:
        return []
    items = list(pool)
    random.shuffle(items)
    by_cat = {}
    for x in items:
        by_cat.setdefault(x[0].category, []).append(x)
    cats = list(by_cat)
    random.shuffle(cats)
    picked = []
    idx = 0
    while len(picked) < n:
        cat = cats[idx % len(cats)]
        if by_cat[cat]:
            picked.append(by_cat[cat].pop())
        idx += 1
    return picked


def _draw_table(candidates, k, meat_ratio):
    """抽取一桌 k 道菜：荤素按比例（k>=2 时至少 1 荤 1 素）、分类尽量分散。候选不足返回 None。"""
    if not candidates or k <= 0 or len(candidates) < k:
        return None
    if k == 1:
        return [random.choice(candidates)]

    meat_n = max(1, min(k - 1, round(k * meat_ratio)))
    meats = [x for x in candidates if x[0].meat_type in ("荤", "半荤素")]
    vegs = [x for x in candidates if x[0].meat_type == "素"]

    # 某类不足时用另一类补足（数据无荤/无素时优雅降级）
    meat_n = min(meat_n, len(meats))
    if len(vegs) < k - meat_n:
        meat_n = k - len(vegs)
    if meat_n < 0 or meat_n > len(meats):
        return None
    veg_n = k - meat_n
    if veg_n < 0 or veg_n > len(vegs):
        return None

    picked = _spread_sample(meats, meat_n) + _spread_sample(vegs, veg_n)
    random.shuffle(picked)
    return picked


def _try_draw(candidates, k, meat_ratio, budget_min, budget_max, retries=50):
    """尝试抽一桌菜使总价落在预算区间内；返回 (picked, total) 或 (None, None)。"""
    for _ in range(retries):
        picked = _draw_table(candidates, k, meat_ratio)
        if picked is None:
            return None, None
        total = sum(d.price or 0 for d, _ in picked)
        if budget_min <= total <= budget_max:
            return picked, round(total, 2)
    return None, None


def _clear_table():
    for key in ("table", "table_total", "table_people"):
        st.session_state.pop(key, None)


def _do_draw(candidates, k, ratio, bmin, bmax, people, reroll=False):
    """执行摇号并把结果（或冲突提示）写入 session_state。"""
    st.session_state.pop("conflict_note", None)
    st.session_state.pop("reroll_note", None)
    if len(candidates) < k:
        _clear_table()
        if reroll:
            st.session_state.reroll_note = "已没有其他选择啦，请放宽筛选条件"
        else:
            st.session_state.conflict_note = (
                f"符合条件的菜品只有 {len(candidates)} 道，不足以搭配 {k} 道菜，请放宽筛选条件"
            )
        return
    picked, total = _try_draw(candidates, k, ratio, bmin, bmax)
    if picked is None:
        _clear_table()
        st.session_state.conflict_note = (
            "⚠️ 在预算区间内无法搭配出满足荤素/分类要求的一桌菜，请放宽预算、减少人数或调整筛选条件"
        )
        return
    st.session_state.table = picked
    st.session_state.table_total = total
    st.session_state.table_people = people


def _apply_mode():
    """按当前模式同步各筛选控件（回调在控件实例化前运行，避免 AlreadyInstantiated）。"""
    preset = MODES[st.session_state.mode]
    st.session_state.price_range = preset["price"]
    st.session_state.max_km = preset["km"]
    st.session_state.people = preset["people"]
    st.session_state.category = preset["category"]
    st.session_state.taste = preset["taste"]
    st.session_state.mode_note = f"当前模式：{st.session_state.mode}，已为您自动调整筛选条件"
    _clear_table()
    st.session_state.pop("conflict_note", None)
    st.session_state.pop("reroll_note", None)


def _reset_filters():
    """一键重置：回到默认模式「单人简餐」并应用其预设，同时清空忌口。"""
    st.session_state.mode = MODE_NAMES[0]
    _apply_mode()
    st.session_state.avoid = []


def _locate_center():
    st.session_state.lat = DEFAULT_CENTER[0]
    st.session_state.lon = DEFAULT_CENTER[1]


# ---- 首次进入：默认第一个模式并同步预设 ----
if "mode" not in st.session_state:
    st.session_state.mode = MODE_NAMES[0]
    _apply_mode()
if "lat" not in st.session_state:
    st.session_state.lat = DEFAULT_CENTER[0]
if "lon" not in st.session_state:
    st.session_state.lon = DEFAULT_CENTER[1]

# ---- 用餐模式 ----
st.subheader("🍽️ 用餐模式")
st.radio("选择模式", MODE_NAMES, key="mode", on_change=_apply_mode, horizontal=True)
if st.session_state.get("mode_note"):
    st.info(st.session_state.mode_note)

# ---- 我的位置 ----
st.subheader("📍 我的位置")
c1, c2, c3 = st.columns([2, 2, 1])
lat = c1.number_input("纬度", format="%.4f", key="lat")
lon = c2.number_input("经度", format="%.4f", key="lon")
c3.button("📍 定位到中原工学院", type="primary", on_click=_locate_center)

# ---- 筛选条件 ----
st.subheader("🔍 筛选条件")
min_price, max_price = st.slider("总预算（元）", 0, 200, step=5, key="price_range")
max_km = st.slider("距离我（公里）内", 0.5, 10.0, step=0.5, key="max_km")
n_people = st.slider("就餐人数", 1, 10, key="people")
st.caption(f"当前范围：中原工学院周边 {max_km:.1f} 公里")

col1, col2 = st.columns(2)
category = col1.multiselect("分类（可多选）", CATEGORIES, key="category")
taste = col2.multiselect("口味", TASTES, key="taste")
avoid = st.multiselect("忌口排除（多选，命中菜名或口味即剔除）", AVOID_OPTIONS, key="avoid")

k = _dish_count(n_people)
ratio = _meat_ratio(MODES[st.session_state.mode]["meat_type"])

# ---- 候选池（按分类/口味/距离筛选；预算按整桌总价校验；聚餐模式剔除早餐品类） ----
dishes = storage.list_dishes(
    category=category or None,
    taste=taste or None,
)
filtered = []
for d in dishes:
    if d.latitude is None or d.longitude is None:
        continue
    # 场景化过滤：非「单人简餐」的聚餐模式剔除纯早餐品类（包子/粥/鸡蛋等）
    if st.session_state.mode != "单人简餐" and _is_breakfast(d.name):
        continue
    # 忌口排除：勾选的忌口命中菜名或口味字段即剔除
    if matches_avoid(d.name, d.taste, avoid):
        continue
    dist = haversine_km(lat, lon, d.latitude, d.longitude)
    if dist <= max_km:
        filtered.append((d, dist))
filtered.sort(key=lambda x: x[1])

st.subheader("🎯 候选菜品")
st.caption(f"当前符合条件：{len(filtered)} 道（按 {n_people} 人需搭配 {k} 道菜）")
if not filtered:
    _clear_table()
    st.warning("⚠️ 没有找到符合条件的菜品，请尝试扩大距离、去掉部分分类、口味或忌口限制。")
    st.button("♻️ 一键重置筛选条件", type="primary", on_click=_reset_filters)
elif len(filtered) < k:
    st.caption("候选不足，摇号时将提示放宽条件。")

# ---- 摇号 / 一键重摇 ----
b1, b2 = st.columns(2)
if b1.button("🎲 摇一摇", type="primary"):
    _do_draw(filtered, k, ratio, min_price, max_price, n_people)
if b2.button("🔄 一键重摇"):
    exclude = {d.id for d, _ in st.session_state.get("table", [])}
    pool = [x for x in filtered if x[0].id not in exclude]
    _do_draw(pool, k, ratio, min_price, max_price, n_people, reroll=True)

if st.session_state.get("conflict_note"):
    st.warning(st.session_state.conflict_note)
if st.session_state.get("reroll_note"):
    st.info(st.session_state.reroll_note)

# ---- 结果与记录 ----
if st.session_state.get("table"):
    st.subheader("🍽️ 为您搭配的一桌菜")
    st.markdown(
        f"### 就餐人数：{st.session_state.table_people} 人 · 这桌菜预估总价：¥{st.session_state.table_total:.1f} 元"
    )
    for d, dist in st.session_state.table:
        st.success(f"**{d.name}** · {d.category} · {d.meat_type} · ¥{d.price or 0:.0f} · 约 {dist:.2f} 公里")
    if st.button("✅ 选定并记录"):
        for d, _ in st.session_state.table:
            storage.add_record(d.id, source="draw")
        _clear_table()
        st.success("已写入选餐记录（可在「记录评价」页查看）")
