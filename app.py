import streamlit as st

from meal_picker_agent.config import DEFAULT_CENTER, get_storage
from meal_picker_agent.seed import seed_demo_data

st.set_page_config(page_title="今天吃什么", page_icon="🍚")

# 启动即自动检测/初始化数据库；空库时自动注入演示数据（云端首次部署同样生效）
storage = get_storage()
seeded = seed_demo_data(storage)

st.title("🍚 今天吃什么")
st.markdown(
    """
    左侧边栏切换模块：
    - 🍽️ **菜品库管理**：录入、批量导入、导出菜品数据
    - 🎲 **智能筛选与摇号**：多条件筛选 + 随机摇号
    - 📝 **记录评价**：选餐记录、打分评价、导出历史
    """
)

st.divider()
st.subheader("📦 数据状态")
dishes = storage.list_dishes()
records = storage.list_records()
c1, c2, c3 = st.columns(3)
c1.metric("菜品数", len(dishes))
c2.metric("选餐记录", len(records))
c3.metric("默认中心", "中原工学院")
st.caption(
    f"数据库 data/meal.db 已自动检测/初始化；默认地理中心 lat={DEFAULT_CENTER[0]}, lng={DEFAULT_CENTER[1]}"
)
if seeded:
    st.success(f"检测到空库，已自动注入 {seeded} 条演示数据（中原工学院周边）。")
