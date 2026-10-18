# 云端部署指南

本指南说明如何把「今天吃什么」部署到云端（以 Streamlit Community Cloud 为例）。

## 一、本地运行（先自测）
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```
浏览器自动打开 `http://localhost:8501`。

## 二、部署文件
| 文件 | 作用 |
| --- | --- |
| `requirements.txt` | 云端安装依赖（streamlit / pandas / openpyxl / requests） |
| `app.py` | 入口页，启动即自动检测/初始化数据库（`data/meal.db`），空库自动注入 93 条演示数据 |
| `pages/` | 三个模块页面（M1 菜品库 / M2 筛选摇号 / M3 记录评价） |

## 三、部署到 Streamlit Community Cloud
1. 把项目推送到 GitHub 仓库（`data/`、`.venv/` 已被 `.gitignore` 忽略，不入库）。
2. 打开 <https://share.streamlit.io>，用 GitHub 账号登录。
3. 点「New app」，选择仓库、分支 `main`、入口文件 `app.py`，点「Deploy」。
4. 部署完成后获得一个公开 URL，三个模块在左侧边栏切换。

## 四、数据库自动检测说明
- 首页 `app.py` 与三个模块页面都会调用 `get_storage()`：自动创建 `data/` 目录与 `data/meal.db`，建表（幂等）。
- 若检测到菜品库为空，`seed.seed_demo_data` 自动注入 **93 条**数据：16 条「中原工学院周边」预设 + 77 条北苑1楼真实采集（从 `samples/beiyuan_1f_menu.csv` 读取，随仓库一起部署），并用自动分类引擎打上「外卖/堂食/家常菜」标签，保证老师打开绝不见空白页面。

## 五、注意事项
- **SQLite 是文件型数据库**：Community Cloud 的实例文件系统是临时的，重启/重新部署后 `data/meal.db` 可能被清空；再次启动会自动重建并重新注入 93 条演示数据，无需人工干预。需要持久化历史时，建议接入外部数据库（如 Supabase / Postgres）。
- 本应用演示采用「离线数据 + 本地导入」，**不会在运行时请求外卖平台**（爬虫脚本 `scripts/fetch_meituan.py` 仅作代码留存，默认离线）。
- 敏感配置（如有）走环境变量，不硬编码到代码。

## 六、常见问题
- **端口 / 入口**：Community Cloud 固定用 `app.py` 作为入口，无需指定端口。
- **依赖缺失**：确认 `requirements.txt` 与 `pyproject.toml` 的依赖一致，重新部署会自动重装。
- **Excel 导入**：依赖 `openpyxl`（已列入 requirements.txt）；CSV 无需额外依赖。
