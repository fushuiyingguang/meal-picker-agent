# docs 索引

本目录存放项目开发的标准文件与模块报告。开发前按主题查阅，变更后保持同步。

## 标准文件
| 主题 | 文件 | 说明 |
| --- | --- | --- |
| 需求规范 | [requirements.md](requirements.md) | 三模块划分、功能需求、验收要求 |
| 技术规范 | [tech-stack.md](tech-stack.md) | Streamlit 多页面 + SQLite，目录与配置约定 |
| 数据结构与接口 | [data-interface.md](data-interface.md) | SQLite 表结构 + 三模块共享接口契约 |
| 设计规范 | [design-spec.md](design-spec.md) | 架构、模块、接口与数据设计原则 |
| 编码规范 | [coding-standards.md](coding-standards.md) | 命名、格式、类型、异常处理约定 |
| 执行步骤规范 | [execution-steps.md](execution-steps.md) | 从需求到交付的标准开发流程 |
| 版本控制规范 | [git-workflow.md](git-workflow.md) | 分支、提交信息与协作约定 |

## 模块报告（每模块一条完整链条）
| 模块 | 文件 |
| --- | --- |
| M1 菜品库管理 | [module1.md](module1.md) |
| M2 智能筛选与摇号 | [module2.md](module2.md) |
| M3 记录评价 | [module3.md](module3.md) |

## 通用约定
- 文档语言：中文。
- 文件名：英文小写，多词用连字符 `-`。
- 含 `TODO:` 标记的条目为待确认项，确认后删除标记并填入具体内容。
