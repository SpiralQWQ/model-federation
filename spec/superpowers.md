# Superpowers 技能清单 — 管线阶段

> **所属管线**：Phase 2（执行）
> **触发方式**：JIT 路由 → "Superpowers"场景（触发词: 超能力/唤醒/执行计划/写测试）
> **用途**：场景与对应技能表，禁止跳过 Skill 工具
> **质量门禁**：Qwen + GLM 各自独立审查，均 ≥9.5 方通过

---

## 场景与对应技能

| 场景 | 必须调用的技能 |
|------|--------------|
| 开始任何新功能/创意 | `brainstorming` |
| 写多步骤实施计划 | `writing-plans` |
| 执行实施计划 | `executing-plans` 或 `subagent-driven-development` |
| 遇到 bug | `systematic-debugging` |
| 声称完成 | `verification-before-completion` |
| 提交代码前 | `requesting-code-review` |
| 收到代码审查反馈 | `receiving-code-review` |

## 自检规则

每次回复前检查当前任务是否匹配上述场景 → 匹配则必须先调用 Skill 工具激活对应 superpowers 技能，再继续。在准备开始写代码或调试前，必须先输出 `<skill_check>` 标签。

## 禁止

跳过 superpowers 技能直接用原生命令替代。

---
## 质检门禁（Phase 3 — Qwen + GLM 各自独立审查，均≥9.5 方通过）

### 检查项细则

| 检查项 | 具体判定标准 | Qwen 评分 | GLM 评分 |
|--------|------------|:---------:|:--------:|
| 技能匹配正确 | 场景对应技能已调用（brainstorming/writing-plans 等）。未调用或错调 → 扣 4 分 | /10 | /10 |
| `<skill_check>` 已输出 | 编代码前已输出 `<skill_check>` 标签。直接写代码无标签 → 扣 3 分 | /10 | /10 |
| 未跳过 Skill 工具 | 未用原生命令替代 Skill 工具。绕过 → 扣 4 分 | /10 | /10 |

### 通过条件

```
Qwen 评分 ≥ 9.5 AND GLM 评分 ≥ 9.5 → [质检] 裁决: 通过
Qwen 评分 < 9.5 OR GLM 评分 < 9.5 → [质检] 裁决: 返工（标注扣分项）
```
