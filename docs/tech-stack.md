# 技术规范

## 语言与版本
- Python 3.11+

## 技术栈（已定）
- 界面：**Streamlit 多页面**（`app.py` 为入口/首页，`pages/` 下每模块一页）。
- 数据：**SQLite**（标准库 `sqlite3`），单文件 `data/meal.db`（git 忽略）。
- 数据模型：`dataclass`（`Dish` / `Record`）。
- 测试：`pytest`（业务逻辑单测；页面层手动验收 + 截图补入报告）。

## 依赖
- 运行：`streamlit`、`pandas`、`openpyxl`（Excel 导入）
- 爬虫脚本（代码留存）：`requests`
- 测试：`pytest`
- 依赖清单：`requirements.txt`（与 `pyproject.toml` 保持一致）

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
│   ├── geo.py                  # Haversine 距离 + 球面偏移
│   ├── seed.py                 # 演示数据（中原工学院周边）
│   └── config.py               # 全局配置（数据库路径 + 默认地理中心）
├── scripts/
│   └── fetch_meituan.py        # 爬虫脚本（仅代码留存，默认离线）
├── samples/
│   └── beiyuan_1f_menu.csv     # 团队实地采集北苑1楼 77 条真实菜品数据
├── data/                       # SQLite 文件（git 忽略）
├── requirements.txt            # 云端部署依赖清单
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
