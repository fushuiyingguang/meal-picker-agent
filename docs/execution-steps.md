# 执行步骤规范

标准开发流程，一次只推进一个稳定步骤。

## 流程
1. **明确需求**：对照 [requirements.md](requirements.md)，确认要做的功能与验收标准；不明确的先澄清。
2. **设计**：按 [design-spec.md](design-spec.md) 确定模块/接口/数据，小改动直接实现，大改动先写设计说明。
3. **实现**：遵循 [coding-standards.md](coding-standards.md) 与 [tech-stack.md](tech-stack.md)。
4. **测试**：补充 `tests/`，本地跑通 `pytest`。
5. **记录**：更新当天 [开发日志](../dev-log/README.md) 的「已完成」。
6. **提交**：按 [git-workflow.md](git-workflow.md) 提交，提交信息说明「做了什么、为什么」。

## 一次只做多少
- 每个步骤产出可运行、可回归的最小增量，不一次性铺开大重构。
- 步骤间留验证点：跑测试 / 手动验证通过后再进入下一步。

## 待办维护
- 会话结束时，把未完成项写入开发日志「待办」，滚动到下一工作日。
