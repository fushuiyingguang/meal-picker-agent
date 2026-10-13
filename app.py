import streamlit as st

st.set_page_config(page_title="今天吃什么", page_icon="🍚")

st.title("🍚 今天吃什么")
st.markdown(
    """
    左侧边栏切换模块：
    - 🍽️ **菜品库管理**：录入、批量导入、导出菜品数据
    - 🎲 **智能筛选与摇号**：多条件筛选 + 随机摇号
    - 📝 **记录评价**：选餐记录、打分评价、导出历史
    """
)
