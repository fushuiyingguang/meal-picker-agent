"""M3 记录评价：选餐历史、打分评价、统计、导出。"""

import sys
from pathlib import Path

# 将项目的 src 目录添加到 Python 搜索路径（页面位于 pages/ 子目录，需向上回溯一层）
src_path = Path(__file__).resolve().parents[1] / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from collections import Counter

import pandas as pd
import streamlit as st

from meal_picker_agent.config import get_storage
from meal_picker_agent.seed import seed_demo_data

st.set_page_config(page_title="记录评价", page_icon="📝")

storage = get_storage()
seed_demo_data(storage)

st.title("📝 记录评价")

# ---- 手动新增 ----
with st.expander("➕ 手动新增选餐记录", expanded=False):
    dishes = storage.list_dishes()
    if dishes:
        dish_name = st.selectbox("选择菜品", [d.name for d in dishes])
        if st.button("新增记录"):
            dish = next(d for d in dishes if d.name == dish_name)
            storage.add_record(dish.id, source="manual")
            st.success(f"已新增：{dish_name}")
            st.rerun()
    else:
        st.info("菜品库为空，请先在「菜品库管理」录入菜品。")

records = storage.list_records()

# ---- 统计 ----
st.subheader("📊 统计")
scores = [r.score for r in records if r.score is not None]
avg = sum(scores) / len(scores) if scores else None
c1, c2, c3, c4 = st.columns(4)
c1.metric("总记录", len(records))
c2.metric("已评分", len(scores))
c3.metric("平均分", f"{avg:.1f}" if avg is not None else "—")
c4.metric("近 7 天已选菜品", len(storage.recent_dish_ids(days=7)))

cat_counter = Counter()
for r in records:
    if r.dish_id is not None:
        d = storage.get_dish(r.dish_id)
        if d:
            cat_counter[d.category] += 1
if cat_counter:
    st.write("分类选择频率：")
    st.dataframe(pd.DataFrame(cat_counter.most_common(), columns=["分类", "次数"]))

# ---- 历史列表 ----
st.subheader("📋 选餐历史")
if not records:
    st.info("还没有选餐记录。去「智能筛选与摇号」摇一摇并选定，或在上方手动新增。")
else:
    df = pd.DataFrame(
        [
            {
                "记录ID": r.id,
                "菜名": r.dish_name,
                "时间": r.selected_at,
                "来源": "摇号" if r.source == "draw" else "手动",
                "评分": r.score if r.score is not None else "",
                "评价": r.rating_note or "",
                "备忘": r.memo or "",
            }
            for r in records
        ]
    )
    # 评分列混有 int 与空字符串，pandas 会推断为 object，pyarrow 渲染时转 int64 报错；
    # 统一转为可空整数：已评分显示数字，未评分显示为空（避免显示误导性的 0）。
    df["评分"] = pd.to_numeric(df["评分"], errors="coerce").astype("Int64")
    st.dataframe(df)

    # 有明显备忘的记录用浅色信息框突出展示
    memos = [(r.id, r.dish_name, r.memo) for r in records if r.memo]
    if memos:
        st.subheader("📝 就餐备忘")
        for rid, dish_name, memo in memos:
            st.info(f"**#{rid} · {dish_name}**\n\n{memo}")

    # ---- 打分评价 ----
    st.subheader("⭐ 打分评价")
    labels = [f"#{r.id} · {r.dish_name} · {r.selected_at}" for r in records]
    # 动态默认值：定位到第一条未评分记录；全部评完则提示
    unrated_idx = next((i for i, r in enumerate(records) if r.score is None), None)
    if unrated_idx is None:
        st.success("🎉 所有记录已评价完毕")
        unrated_idx = 0
    pick = st.selectbox("选择要评价的记录", labels, index=unrated_idx, key="rate_pick")
    idx = labels.index(pick)
    rec = records[idx]
    rid = rec.id
    score = st.slider("评分（1-5）", 1, 5, rec.score or 3, key=f"score_{rid}")
    note = st.text_input("评价（可选）", value=rec.rating_note or "", key=f"note_{rid}")
    if st.button("保存评价", type="primary"):
        storage.set_rating(rid, score, note)
        st.session_state.pop("rate_pick", None)  # 清空选中态，让 index 在 rerun 后重新定位到下一条未评分
        st.success("已保存评价")
        st.rerun()

    # ---- 就餐备忘（独立保存，不干扰打分跳转） ----
    memo = st.text_area("📝 就餐备忘/感受（可选）", value=rec.memo or "", key=f"memo_{rid}", height=90)
    if st.button("保存备忘"):
        storage.set_memo(rid, memo.strip())
        st.success("已保存备忘")
        st.rerun()

    # ---- 导出 ----
    st.subheader("📤 导出历史")
    col_csv, col_json = st.columns(2)
    col_csv.download_button(
        "下载 CSV",
        data=storage.export_records("csv").encode("utf-8-sig"),
        file_name="records.csv",
        mime="text/csv",
    )
    col_json.download_button(
        "下载 JSON",
        data=storage.export_records("json").encode("utf-8"),
        file_name="records.json",
        mime="application/json",
    )
