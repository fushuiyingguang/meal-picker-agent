"""M2 智能筛选与摇号：用餐模式 + 多条件 + 位置距离筛选 + 随机摇号 + 一键重摇。"""

import random

import streamlit as st

from meal_picker_agent.config import DEFAULT_CENTER, get_storage
from meal_picker_agent.geo import haversine_km
from meal_picker_agent.seed import seed_demo_data

st.set_page_config(page_title="智能筛选与摇号", page_icon="🎲")

CATEGORIES = ["中餐", "快餐", "面食", "小吃", "西餐", "粥品", "甜点", "烧烤"]
TASTES = ["辣", "麻", "清淡", "甜", "咸", "酸"]
MEAT_TYPES = ["荤", "素", "半荤素"]

# 五种用餐模式预设：预算区间（元）、距离（公里）、口味、荤素、分类
MODE_NAMES = ["单人简餐", "朋友小聚", "家庭聚餐", "公司聚餐", "社团团建"]
MODES = {
    "单人简餐": {"price": (10, 25), "km": 1.0, "taste": ["清淡", "咸"], "meat_type": "全部", "category": []},
    "朋友小聚": {"price": (20, 60), "km": 3.0, "taste": [], "meat_type": "荤", "category": ["小吃", "烧烤"]},
    "家庭聚餐": {"price": (30, 100), "km": 5.0, "taste": [], "meat_type": "全部", "category": []},
    "公司聚餐": {"price": (50, 150), "km": 5.0, "taste": [], "meat_type": "荤", "category": ["中餐", "快餐"]},
    "社团团建": {"price": (30, 80), "km": 3.0, "taste": [], "meat_type": "全部", "category": ["烧烤", "小吃"]},
}

storage = get_storage()
seed_demo_data(storage)

st.title("🎲 智能筛选与摇号")


def _apply_mode():
    """按当前模式同步各筛选控件（回调在控件实例化前运行，避免 AlreadyInstantiated）。"""
    preset = MODES[st.session_state.mode]
    st.session_state.price_range = preset["price"]
    st.session_state.max_km = preset["km"]
    st.session_state.meat_type = preset["meat_type"]
    st.session_state.category = preset["category"]
    st.session_state.taste = preset["taste"]
    st.session_state.mode_note = f"当前模式：{st.session_state.mode}，已为您自动调整筛选条件"


def _reset_filters():
    """一键重置：回到默认模式「单人简餐」并应用其预设。"""
    st.session_state.mode = MODE_NAMES[0]
    _apply_mode()


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
min_price, max_price = st.slider("预算（元）", 0, 200, step=5, key="price_range")
max_km = st.slider("距离我（公里）内", 0.5, 10.0, step=0.5, key="max_km")
st.caption(f"当前范围：中原工学院周边 {max_km:.1f} 公里")

col1, col2 = st.columns(2)
category = col1.multiselect("分类（可多选）", CATEGORIES, key="category")
meat_type = col1.selectbox("荤素", ["全部"] + MEAT_TYPES, key="meat_type")
taste = col2.multiselect("口味", TASTES, key="taste")
count = col2.slider("摇出数量", 1, 5, 1)

# ---- 实时筛选（切换模式后自动重新计算） ----
dishes = storage.list_dishes(
    category=category or None,
    taste=taste or None,
    meat_type=None if meat_type == "全部" else meat_type,
    min_price=min_price,
    max_price=max_price,
)
filtered = []
for d in dishes:
    if d.latitude is None or d.longitude is None:
        continue
    dist = haversine_km(lat, lon, d.latitude, d.longitude)
    if dist <= max_km:
        filtered.append((d, dist))
filtered.sort(key=lambda x: x[1])

st.subheader("🎯 候选菜品")
st.caption(f"当前符合条件：{len(filtered)} 道")
if filtered:
    st.dataframe(
        [
            {
                "菜名": d.name,
                "分类": d.category,
                "荤素": d.meat_type,
                "价格(元)": d.price,
                "距离(公里)": round(dist, 2),
            }
            for d, dist in filtered
        ]
    )
else:
    # 条件冲突提示：空结果时给出兜底，避免用户陷入死胡同
    st.session_state.pop("picked", None)
    st.session_state.pop("reroll_note", None)
    st.warning("⚠️ 没有找到符合条件的菜品，请尝试放宽预算、扩大距离或去掉部分口味限制。")
    st.button("♻️ 一键重置筛选条件", type="primary", on_click=_reset_filters)

# ---- 摇号 / 一键重摇 ----
b1, b2 = st.columns(2)
if b1.button("🎲 摇一摇", type="primary"):
    st.session_state.pop("reroll_note", None)
    if not filtered:
        st.session_state.pop("picked", None)
    else:
        st.session_state.picked = list(random.sample(filtered, min(count, len(filtered))))
if b2.button("🔄 一键重摇"):
    exclude = {d.id for d, _ in st.session_state.get("picked", [])}
    pool = [x for x in filtered if x[0].id not in exclude]
    if not pool:
        st.session_state.reroll_note = "已没有其他选择啦，请放宽筛选条件"
    else:
        st.session_state.picked = list(random.sample(pool, 1))
        st.session_state.pop("reroll_note", None)

if st.session_state.get("reroll_note"):
    st.info(st.session_state.reroll_note)

# ---- 结果与记录 ----
if "picked" in st.session_state and st.session_state.picked:
    st.subheader("🎯 摇号结果")
    for d, dist in st.session_state.picked:
        st.success(f"**{d.name}** · {d.category} · {d.meat_type} · 约 {dist:.2f} 公里 · ¥{d.price or 0:.0f}")
    if st.button("✅ 选定并记录"):
        for d, _ in st.session_state.picked:
            storage.add_record(d.id, source="draw")
        st.session_state.picked = []
        st.success("已写入选餐记录（可在「记录评价」页查看）")
