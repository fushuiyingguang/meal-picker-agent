# 技术规范

## 语言与版本
- Python 3.11+

## 技术栈（已定）
- 界面：**Streamlit 多页面**（`app.py` 为入口/首页，`pages/` 下每模块一页）。
- 数据：**SQLite**（标准库 `sqlite3`），单文件 `data/meal.db`（git 忽略）。
- 数据模型：`dataclass`（`Dish` / `Record`）。
- 测试：`pytest`（业务逻辑单测；页面层手动验收 + 截图补入报告）。

## 依赖
- 运行：`streamlit`
- 测试：`pytest`

## 依赖管理
- `pyproject.toml` + 虚拟环境（`venv` 或 `uv`），锁文件提交保证可复现。

## 目录结构
```
meal-picker-agent/
├── app.py                      # Streamlit 入口 / 首页
├── pages/
│   ├── 1_dishes.py             # M1 菜品库管理
│   ├── 2_picker.py             # M2 智能筛选与摇号
│   └── 3_records.py            # M3 记录评价
├── src/meal_picker_agent/
│   ├── storage.py              # 共享数据访问层（接口见 docs/data-interface.md）
│   ├── models.py               # Dish / Record 数据模型
│   └── service/                # 各模块业务逻辑（筛选/摇号/统计）
├── data/                       # SQLite 文件（git 忽略）
├── tests/
├── docs/
└── dev-log/
```

## 环境与配置
- 数据库路径等配置集中管理（常量或环境变量），不散落业务代码。
- `data/`、`.env` 不入库（见 .gitignore）。

## 质量工具
- 格式化：`ruff format`
- 静态检查：`ruff`
- 测试：`pytest`
