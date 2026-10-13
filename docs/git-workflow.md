# 版本控制规范

## 分支策略（单人/小团队）
- `main`：始终可运行、可交付的稳定分支。
- 功能开发用短分支（如 `feat/xxx`、`fix/xxx`），完成后合并回 `main`。

## 提交信息
- 格式：`<type>: <简短描述>`，type 可选 `feat` / `fix` / `docs` / `refactor` / `test` / `chore`。
- 描述用中文，说明「做了什么」；必要时正文补充「为什么」。

## 提交时机
- 一个逻辑变更一个提交，不在一个提交里混入无关改动。
- 提交前跑测试，保证 `main` 稳定。

## 常见操作
```bash
git status              # 查看改动
git diff                # 查看差异
git add <file>          # 暂存
git commit -m "feat: ..."   # 提交
```

## 安全
- 不提交密钥、`.env`、个人数据（已在 .gitignore）。
