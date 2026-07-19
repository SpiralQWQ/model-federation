# CLAUDE.md — 全局配置 V7.0

> **安装**：复制此文件到 `~/.claude/CLAUDE.md`，同时将 `spec/` 目录复制到项目根目录（用于 JIT 路由表的场景加载）。  
> Model Federation V7.0 的 AI 辅助配置文件。采用「核心规则 + JIT 路由表 + spec/ 目录」模块化架构，取代 V6.0 的 627 行单体配置。

---

## 基础规则

- 始终用**中文**回复，回答简洁结构化。
- 编辑前先读懂现有结构和代码风格，不做超出任务范围的抽象或重构。
- 英文术语保留，附中文简要说明。
- 用户画像：产品经理思维，挖掘模糊描述下的真实意图，用非技术语言确认。

## 架构冻结 (Configuration Freeze)

以下文件已锁定，严禁擅自修改：路由脚本（`scripts/*_router.py`）、MCP 配置（`.mcp.json`）、CLAUDE.md、settings.json。  
任何对冻结文件的变更必须走「高危操作确认流程」：披露 → 预览 diff → **显式等待用户确认**（如「Go」「确认」） → 验证落地。

## 标准化业务交付格式

技术任务回答仅包含三部分：

1. **YAML 意图块** — 证明协同判定（见下方 Intent Sniffer）
2. **代码方案** — 最终业务代码（Diff 格式，禁止整文件重写）
3. **协同举证** — 日志路径 + 模型分工摘要

> 原则：代码 > 废话。审查/会诊类报告不受此限制。

## 自主意图嗅探器 (Intent Sniffer V7.0)

每次回答最前面必须打印 YAML 块：

```yaml
Intent_Sniffer:
  Domain: [Coding / Reasoning / Vision / Daily]
  Need_Synergy: [True / False]
  Reason: "简述判定原因..."
```

**显式指令优先**：`/代码` `/coding` → Coding · `/推理` `/reasoning` → Reasoning · `/三方` → Tri-Party · `/四方` → Four-Party

**隐式判定**：代码生成/重构/Bug 修复/架构设计 → Coding；算法推导/方案对比 → Reasoning；图片/视频 → Vision；闲聊/查询 → Daily（免协同）

**Need_Synergy**：跨文件修改（>3 文件）、架构决策、性能优化、配置变更 → True；简单修改、纯查询 → False

## 模型选择铁律

1. **绝对锁定**：用户选定模型后，AI 绝对不得擅自更换。
2. **子任务继承**：子 Agent 默认继承显式指定模型；不兼容时降级告警，禁止崩溃。
3. **异常处理**：超时/报错 → 如实报告 → 提供替代列表 → **禁止 AI 自行切换**。
4. **熔断兜底**：连续 2 次全部失败 → `FATAL_ERROR`，挂起会话。

## GLM 质检门禁 V7.0

直写操作（配置文件修改 / CLAUDE.md 变更 / 模板文件编辑 / Git 提交前）必须经 GLM 质检评分 **≥ 9.8/10** 才能执行。

**执行流程**：
1. **方案起草** — 你制定修改方案
2. **GLM 质检** — 调用 GLM 从四维度评分
3. **门禁判断** — ≥ 9.8 允许执行；< 9.8 修订后重新提交
4. **落地** — 通过后方可写入

**四维度评分**：

| 维度 | 说明 |
|------|------|
| 必要性 | 该修改是否必要？有无更简单替代方案？ |
| 正确性 | 逻辑是否正确？格式是否规范？ |
| 安全性 | 是否存在密钥泄漏、权限越界风险？ |
| 完整性 | 是否遗漏前置条件或依赖配置？ |

## 量化数据采集 V7.0

若已安装 ActivityWatch + onefetch，可自动为日志注入量化数据。

```
ActivityWatch ─┐
onefetch ──────┤→ collect_daily_data.ps1 → daily_data_YYYY-MM-DD_HHmm.json → 日志归档
git log ───────┤
终端历史 ───────┘
```

**映射**：`time_tracking.*_minutes` → 变更记录 · `git_stats.files_*` → 变更记录(commits>0) · `repo_snapshot.linesOfCode/filesCount/authorsCount` → 快照字段  
**配置一致性检查**：检查 `collect/activity_categories.json` 和 `collect/sensitive_patterns.json` 是否存在。日志模板的量化数据融合规则见 dev-log-tool 的 `spec/log_templates.md`。

## 密钥遮蔽铁律

- 日志、配置、脚本中**严禁出现任何密钥明文**（API Key、Token、密码等）
- 出现密钥的位置必须用 `***` 打码：`API Key = sk-abc***xyz`
- 公钥（`.pub` 文件）和指纹哈希不在遮蔽范围内

## JIT 路由表

> **铁律**：匹配场景时**必须先读取 `spec/<文件>.md`**，未读严禁执行。按 [全局规则] > [协同协议] > [执行模板] 优先级。首次使用前 `ls spec/` 验证文件就位。

| 场景 | 触发条件 | 读取文件 |
|------|---------|---------|
| 三方/四方协同 | 提及"三方/四方"或大规模重构（>3 文件） | `spec/collaboration.md` |
| 代码审查 | 提及"审查/Review/CR" | `spec/code_review.md` |
| Superpowers | 提及"超能力/执行计划/写测试" | `spec/superpowers.md` |
| 图片/视觉 | 图片附件或"看图" | `spec/vision_rules.md` |
| 图片/视频生成 | 提及"生成/画图/做视频" | `spec/image_gen.md` |
| 百炼 DashScope | 提及"百炼/DashScope/双引擎" | `spec/dual_engine.md` |
| GLM 调用 | 提及"GLM/智谱" | `spec/glm_routing.md` |
| OpenCode | 提及"opencode" | `spec/opencode_routing.md` |
| 日志模板 | 提及"日志/归档" | `spec/log_templates.md` |
| 数据采集 | 提及"采集/collect" | `spec/data_toolchain.md` |
| Token 计费 | 提及"计费/账单" | `spec/billing_rules.md` |
| 安全审计 | 提及"审计/检查漏洞" | `spec/code_review.md` |
| 跨文件重构 | 提及"重构整个项目" | `spec/collaboration.md` |

**spec/ 目录结构**（需自行创建，每个文件 30-80 行）：
```
spec/
├── collaboration.md     # 三方/四方协同协议
├── code_review.md       # 代码审查清单
├── superpowers.md       # Superpowers 技能清单
├── vision_rules.md      # 多模态视觉规则
├── image_gen.md         # 生图生视频管线
├── dual_engine.md       # 百炼 DashScope 路由
├── glm_routing.md       # GLM 模型路由
├── opencode_routing.md  # OpenCode 模型路由
├── log_templates.md     # 日志模板
├── data_toolchain.md    # 数据采集工具链
└── billing_rules.md     # Token 计费规则
```

---

## 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| V7.0 | 2026-07 | **架构重构**：627 行单体 → 核心规则(~120 行) + JIT 路由表 + spec/ 模块化目录；新增 GLM 质检门禁、量化数据采集、密钥遮蔽铁律 |
| V6.0 | 2026-06 | 三方协同、GLM 路由、四方会诊、计费播报 |
| V5.x | 2026-05 | 早期架构：三方联邦、Superpowers、防作弊透传协议 |
