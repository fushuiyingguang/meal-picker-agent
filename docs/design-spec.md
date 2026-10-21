# 设计规范

## 设计原则
1. **单一职责**：模块/函数只做一件事，边界清晰。
2. **依赖方向**：页面层 → 业务层 → 数据层，单向依赖，页面不直接写 SQL、不跨页面互相调用。
3. **可测试优先**：核心逻辑（算法 / 工具函数）不依赖 I/O，便于单元测试。
4. **最小实现**：先用最简单方案满足当前需求，不过度设计。

## 架构分层（已落地）
| 层 | 职责 | 对应代码 |
| --- | --- | --- |
| 页面层 | Streamlit 三页，只做交互与展示 | `app.py` + `pages/1_dishes.py` / `2_picker.py` / `3_records.py` |
| 业务层 | 决策算法与工具（Haversine、自动分类、忌口匹配、摇号） | `src/meal_picker_agent/geo.py` / `utils.py` |
| 数据层 | SQLite 持久化与共享接口 | `src/meal_picker_agent/storage.py` / `models.py` / `config.py` / `seed.py` |

## 前端 UI 布局原则（Streamlit）
- 一页一模块：页面顶部 `st.set_page_config` 设定标题 / 图标，正文用 `st.title`。
- 低频操作（录入、批量导入、删除）折叠进 `st.expander`；高频展示（列表、摇号结果、历史）置于正文。
- 交互统一用 Streamlit 原生组件（`form` / `button` / `slider` / `selectbox` / `multiselect` / `dataframe`），不引入前端框架。
- 用户反馈用 `st.success` / `st.warning` / `st.error` / `st.info` 区分语义；需刷新状态的操作用 `st.rerun()`。

## 数据库表结构设计
- 单文件 SQLite `data/meal.db`（git 忽略），首次启动自动建表，旧库用 `ALTER TABLE` 幂等补列。
- `dishes`：菜名唯一；含分类 / 价格 / 口味 / 荤素 / 距离 / 经纬度。
- `records`：选餐历史快照（菜名留存，菜品删除后历史不丢）+ 评分 / 评价 / 备忘。
- 完整字段与接口契约见 [data-interface.md](data-interface.md)。

## 接口与数据设计
- 三页面统一通过 `storage.py` 读写数据，不直接写 SQL、不跨页面互调（接口契约见 [data-interface.md](data-interface.md)）。
- 数据模型用 `dataclass`（`Dish` / `Record`）明确定义字段与类型。

## 错误处理
- 业务异常使用自定义异常类（`StorageError`），由页面层捕获并转换为用户可读信息。
- 不吞异常；外部调用失败需重试或明确失败原因。
- 爬虫等不可靠外部来源必须提供本地降级兜底，保证主流程不崩溃。

## 日志
- 使用标准 `logging`，区分 `DEBUG/INFO/WARNING/ERROR`。
- 日志不得包含敏感信息（密钥、个人隐私）。
