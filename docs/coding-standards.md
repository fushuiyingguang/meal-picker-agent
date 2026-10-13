# 编码规范

## 命名
- 模块/文件：`snake_case.py`
- 类：`PascalCase`
- 函数/变量：`snake_case`
- 常量：`UPPER_SNAKE_CASE`
- 私有成员：单下划线前缀 `_internal`

## 格式
- 统一用 `ruff format`（或 `black`），提交前先格式化。
- 行宽建议 100 字符。

## 类型注解
- 公开函数/方法必须有参数与返回值类型注解。
- 数据模型优先使用 `dataclass` 或 `pydantic`。

## 异常处理
- 不写裸 `except:`；捕获具体异常。
- 需要清理资源时使用上下文管理器（`with` / `contextlib`）。

## 注释与文档
- 注释解释「为什么」，不重复代码「做什么」。
- 公开模块/函数写简短 docstring。
- 注释语言：中文。

## 测试
- 每个新增业务逻辑应有对应单元测试。
- 测试文件命名 `test_*.py`，用 `pytest`。

## 安全检查清单
- 不硬编码密钥/token；不进 `print` 敏感信息。
- 外部输入必须校验，SQL 使用参数化（如需数据库）。
