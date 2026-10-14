# 项目总结报告：「今天吃什么」

## 一、项目概述
「今天吃什么」是面向校园场景的决策辅助工具，围绕**中原工学院（郑州龙湖校区）**周边饮食，通过「菜品库 → 多条件筛选与摇号 → 记录评价」三个模块形成完整闭环，帮助用户快速决定「今天吃什么」，并避免近期重复。

## 二、技术实现
- 语言/版本：Python 3.11+
- 界面：Streamlit 多页面（`app.py` 入口 + `pages/` 三模块各一页）
- 数据：SQLite（标准库 `sqlite3`，单文件 `data/meal.db`）
- 数据模型：`dataclass`（`Dish` / `Record`）
- 地理：Haversine 距离 + 球面偏移（`geo.py`），默认中心中原工学院 (34.626, 113.705)
- 质量：pytest 单测 + ruff 静态检查

## 三、模块交付
| 模块 | 页面 | 状态 | 报告 |
| --- | --- | --- | --- |
| M1 菜品库管理 | `pages/1_dishes.py` | ✅ | [module1.md](module1.md) |
| M2 智能筛选与摇号 | `pages/2_picker.py` | ✅ | [module2.md](module2.md) |
| M3 记录评价 | `pages/3_records.py` | ✅ | [module3.md](module3.md) |

## 四、数据
- 演示数据：16 条「中原工学院周边」预设菜品（含经纬度，围绕中心 5 公里内分布），空库自动注入。
- 真实数据：团队实地采集北苑 1 楼 7 个档口共 77 条真实菜品数据，见 `samples/beiyuan_1f_menu.csv`（经纬度统一 34.628, 113.702，约距中心 350 米），可在 M1 批量导入。

## 五、部署
- 依赖：`requirements.txt`（streamlit / pandas / openpyxl / requests）。
- 入口 `app.py` 启动即自动检测/初始化数据库，空库自动注入演示数据。
- 详见 [deploy-guide.md](deploy-guide.md)。

## 六、测试结论
- pytest：全量用例通过（含经纬度读写、地理计算、种子数据 5 公里分布、77 条样例校验）。
- ruff：静态检查通过。
- 页面：M1/M2/M3 均通过 Streamlit AppTest 无头冒烟验证。

## 七、后续可迭代方向
- M2 模式切换（随便吃/清淡/按预算）、不重复推荐接入摇号。
- M3 更丰富的统计图表。
- 云端持久化数据库（如 Supabase / Postgres）替代临时 SQLite 文件。
