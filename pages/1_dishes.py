"""M1 菜品库管理：录入、批量导入、导出、演示数据。"""

import pandas as pd
import streamlit as st

from meal_picker_agent.config import get_storage
from meal_picker_agent.models import Dish
from meal_picker_agent.seed import seed_demo_data
from meal_picker_agent.storage import StorageError

st.set_page_config(page_title="菜品库管理", page_icon="🍽️")

CATEGORIES = ["中餐", "快餐", "面食", "小吃", "西餐", "粥品", "甜点", "烧烤", "外卖", "堂食", "家常菜"]
TASTES = ["辣", "麻", "清淡", "甜", "咸", "酸"]
MEAT_TYPES = ["荤", "素", "半荤素"]


def _parse_taste(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return [t.strip() for t in str(value).replace("/", ",").replace("、", ",").split(",") if t.strip()]


def _to_float(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    return float(s) if s else None


def _parse_coord(value):
    s = "" if value is None else str(value).strip()
    if not s:
        return None
    return float(s)


def _import_dataframe(storage, df):
    count = 0
    errors = []
    for _, row in df.iterrows():
        try:
            dish = Dish(
                id=None,
                name=str(row["name"]).strip(),
                category=str(row["category"]).strip(),
                price=_to_float(row.get("price")),
                taste=_parse_taste(row.get("taste")),
                meat_type=str(row.get("meat_type") or "").strip(),
                distance=_to_float(row.get("distance")),
                latitude=_to_float(row.get("latitude")),
                longitude=_to_float(row.get("longitude")),
            )
            storage.add_dish(dish)
            count += 1
        except (StorageError, KeyError, ValueError) as exc:
            errors.append(f"{row.get('name', '?')}: {exc}")
    return count, errors


storage = get_storage()
seed_demo_data(storage)  # 空库时自动注入演示数据

st.title("🍽️ 菜品库管理")

# ---- 录入 ----
with st.expander("➕ 录入单个菜品", expanded=True):
    with st.form("add_dish_form"):
        col1, col2 = st.columns(2)
        name = col1.text_input("菜名 *")
        category = col2.selectbox("分类 *", CATEGORIES)
        price = col1.number_input("价格（元）", min_value=0.0, value=15.0, step=0.5)
        distance = col2.number_input("距离（米）", min_value=0.0, value=500.0, step=50.0)
        taste = st.multiselect("口味", TASTES)
        meat_type = st.selectbox("荤素", MEAT_TYPES)
        lat_s = col1.text_input("纬度（可选）", placeholder="如 31.2304")
        lon_s = col2.text_input("经度（可选）", placeholder="如 121.4737")
        submitted = st.form_submit_button("保存")
    if submitted:
        if not name.strip():
            st.error("菜名不能为空")
        else:
            try:
                storage.add_dish(
                    Dish(
                        id=None,
                        name=name.strip(),
                        category=category,
                        price=price,
                        taste=taste,
                        meat_type=meat_type,
                        distance=distance,
                        latitude=_parse_coord(lat_s),
                        longitude=_parse_coord(lon_s),
                    )
                )
                st.success(f"已保存：{name.strip()}")
            except (StorageError, ValueError) as exc:
                st.error(str(exc))

# ---- 批量导入 ----
with st.expander("📥 批量导入（CSV / Excel）"):
    uploaded = st.file_uploader("上传文件", type=["csv", "xlsx", "xls"])
    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            st.write("预览：", df.head())
            if st.button("确认导入"):
                count, errors = _import_dataframe(storage, df)
                st.success(f"成功导入 {count} 条")
                if errors:
                    st.warning("部分失败：" + "；".join(errors[:5]))
        except Exception as exc:  # noqa: BLE001
            st.error(f"读取失败：{exc}")

# ---- 列表 ----
st.subheader("菜品列表")
dishes = storage.list_dishes()
if not dishes:
    st.info("暂无菜品，请录入或导入。")
else:
    df = pd.DataFrame(
        [
            {
                "ID": d.id,
                "菜名": d.name,
                "分类": d.category,
                "价格": d.price,
                "口味": "、".join(d.taste),
                "荤素": d.meat_type,
                "距离(米)": d.distance,
                "纬度": d.latitude,
                "经度": d.longitude,
            }
            for d in dishes
        ]
    )
    st.dataframe(df)

    st.download_button(
        "下载菜品库 CSV",
        data=storage.export_dishes("csv").encode("utf-8-sig"),
        file_name="dishes.csv",
        mime="text/csv",
    )

    # ---- 删除 ----
    with st.expander("🗑️ 删除菜品"):
        names = [d.name for d in dishes]
        to_delete = st.selectbox("选择要删除的菜品", names)
        confirm = st.checkbox("确认删除（历史选餐记录会保留）")
        if st.button("删除", type="primary") and confirm:
            dish_id = next(d.id for d in dishes if d.name == to_delete)
            storage.delete_dish(dish_id)
            st.success(f"已删除：{to_delete}")
            st.rerun()
