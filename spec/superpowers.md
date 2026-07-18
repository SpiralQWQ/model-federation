# 超能力 (Superpowers) — 技能清单与选用规则

> 代码相关任务一律优先使用 Superpowers 技能，禁止用原生低效命令替代。

## 技能清单

| 技能 | 场景 | 动作 |
|------|------|------|
| `brainstorming` | 方案设计、架构选型、多种思路对比 | 先发散再收敛，输出决策树 |
| `writing-plans` | 确定方案后编写执行计划 | 分步骤、分责任人、可验证 |
| `executing-plans` | 按计划执行代码修改 | 严格遵循计划，不跳跃步骤 |
| `test-driven-development` | 新功能开发、需要测试覆盖 | 先写测试，再写实现 |
| `systematic-debugging` | Bug 排查、根因分析 | 二分法定位 + 假设验证循环 |
| `verification-before-completion` | 修改完成后验证正确性 | 执行验证命令 + 结果比对 |
| `code-review` | 提交前/PR 前代码审查 | 差异审查 + 严重度分级 |

## 选用原则

- 实作类任务（改代码）：先 `brainstorming` → `writing-plans` → `executing-plans` / `test-driven-development`
- 排查类任务（找 Bug）：`systematic-debugging` → 修复 → `verification-before-completion`
- 提交前：`code-review` → `verification-before-completion`

## 技能自查规则

启动任务时，**必须**在 Intent Sniffer 之后立即检查：

1. 当前任务是否匹配上述技能场景？
2. 如果是 → 拉起对应技能（Skill tool），由技能指令接管执行流程
3. 如果否 → 继续走常规流程
4. 未拉起且事后发现本应拉起 → 视为违反协议

## 禁止行为

- 禁止在匹配 Superpowers 场景时直接用 Edit/Write 修改代码而不走技能流程
- 禁止跳过 `verification-before-completion` 直接结束任务
- 禁止在 `brainstorming` 阶段直接进入实作
