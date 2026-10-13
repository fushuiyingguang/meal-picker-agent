# meal-picker-agent

「今天吃什么」决策辅助工具：Python + Streamlit 多页面，含三个可独立运行/验收的模块（菜品库管理 / 智能筛选与摇号 / 记录评价），共享 SQLite 数据。

## 项目结构
- `app.py` + `pages/` — Streamlit 多页面，三模块各一页
- `src/meal_picker_agent/` — 共享数据访问层与业务逻辑（接口契约见 docs/data-interface.md）
- `data/` — SQLite 文件（git 忽略）
- `docs/` — 项目标准文件与三份模块报告
- `dev-log/` — 开发日志，按天记录「已完成」与「待办」
- `tests/` — 测试

## 标准文件路径（开发前必读对应主题）
| 主题 | 文件 |
| --- | --- |
| 文档索引 | [docs/README.md](docs/README.md) |
| 需求规范 | [docs/requirements.md](docs/requirements.md) |
| 技术规范 | [docs/tech-stack.md](docs/tech-stack.md) |
| 数据结构与接口 | [docs/data-interface.md](docs/data-interface.md) |
| 设计规范 | [docs/design-spec.md](docs/design-spec.md) |
| 编码规范 | [docs/coding-standards.md](docs/coding-standards.md) |
| 执行步骤规范 | [docs/execution-steps.md](docs/execution-steps.md) |
| 版本控制规范 | [docs/git-workflow.md](docs/git-workflow.md) |
| M1 模块报告 | [docs/module1.md](docs/module1.md) |
| M2 模块报告 | [docs/module2.md](docs/module2.md) |
| M3 模块报告 | [docs/module3.md](docs/module3.md) |

## 工作说明
1. 每次开发前，先读对应主题的 `docs/` 标准文件，按规范执行。
2. 三个页面只通过 `src/meal_picker_agent/storage.py` 访问数据，不直接写 SQL、不跨页面互相调用。
3. 遵循 [docs/execution-steps.md](docs/execution-steps.md) 的开发流程，一次只推进一个稳定步骤。
4. 每个会话必须维护开发日志（见下方「开发日志规范」）。
5. 功能完成后补充 `tests/` 并跑通，再提交；页面完成后把截图补入对应模块报告。
6. 提交代码遵循 [docs/git-workflow.md](docs/git-workflow.md)。

## 开发日志规范（每个会话必须执行）
- **会话开始时**：打开/新建当天日志 `dev-log/YYYY-MM-DD.md`（以当天实际日期为准，格式见 [dev-log/README.md](dev-log/README.md)），回顾上一次「待办」。
- **会话进行中**：把已完成事项随时补进「已完成」。
- **会话结束时**：把未完成或下一步事项写入「待办」；未完成项应滚动到下一个工作日日志。
- 语言：中文。
