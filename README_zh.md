<p align="center">
  <img src="cover_seedream.png" alt="Model Federation V7.0" width="800">
</p>

<p align="center">
  <kbd>🇨🇳 中文</kbd> · <a href="README.md"><kbd>🇺🇸 English</kbd></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-7.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform">
</p>

<h1 align="center">Model Federation V7.0</h1>
<p align="center"><b>Claude Code 本地多模型联邦 Agent 架构</b></p>

<p align="center">
  <i>DeepSeek 决策调度 · Qwen 主刀手术 · GLM 质检挑刺 · Gemini 安全审计<br>
  四个 AI 模型，一套防偷懒管线，零未审查代码提交。</i>
</p>

---

## 它做什么

你在 Claude Code 里写代码。你提一个问题。在回答离开终端之前，系统已经做了这些事：

| 步骤 | 动作 |
|:--:|------|
| 🔍 | **嗅探**意图 —— 这是写代码？改架构？修 Bug？还是纯闲聊？ |
| 🧵 | **提取**真实源码（绝不发送摘要给模型） |
| 🔧 | **调度** Qwen 重构/优化（主刀） |
| 🔬 | **调度** GLM 找边界条件、死锁风险、缺失注释（质检） |
| ⚖️ | **仲裁** —— DeepSeek 评判双方输出，采纳对的，驳回错的 |
| 📝 | **日志**落盘到 Markdown 文件 —— 不可篡改的审查证据 |
| 🎫 | **签发通行证** —— 没它，Edit/Write/git-commit 全部物理拦截 |
| 📊 | **量化采集** — ⭐ **V7.0 新增** — ActivityWatch + onefetch + git 数据自动归档 |

## 架构

```
用户提问
    │
    ▼
┌──────────────────────────────────────┐
│        意图嗅探器 (DeepSeek)           │
│   "代码？推理？视觉？闲聊？"            │
└──────────┬───────────────────────────┘
           │
    ┌──────▼──────┐     ┌──────────────┐     ┌─────────────┐
    │  Qwen 百炼   │ ──▶ │  GLM 智谱     │ ──▶ │  DeepSeek   │
    │  主刀医生     │     │  质检护士      │     │  仲裁官      │
    │  (qwen3-     │     │  (glm-4.5-air │     │  (v4-pro)   │
    │   coder-plus)│     │   / glm-4.7)  │     │             │
    └──────┬───────┘     └──────┬───────┘     └──────┬──────┘
           │                    │                     │
           └────────────────────┴─────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  物理日志 + 通行证签发   │
                    │  + 量化数据采集 (V7.0)  │
                    └───────────────────────┘

关键词「四方」──▶ + Gemini 3.5 Flash (安全合规官)
```

### 通行证锁（物理拦截）

```
Edit/Write 前  ──▶ check_synergy_ticket.py ──▶ 无证? BLOCKED
git commit 前  ──▶ pre-commit hook          ──▶ 无证? BLOCKED
commit 完成后   ──▶ post-commit              ──▶ 通行证核销
```

这不是「请记住」的软约束。这是操作系统级的物理拦截。

---

## 安装

### 环境要求

| 项目 | 最低版本 | 检查方式 |
|------|:--:|------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| Claude Code | 最新 | `claude --version` |
| 操作系统 | Windows 10+ / macOS 12+ / Ubuntu 20.04+ | — |

> ℹ️ 零第三方 Python 依赖。所有路由脚本仅使用标准库。唯一可选依赖：`Pillow`（图片缩放在 vision_analyzer 中）。

### 第一步 —— 安装 Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

### 第二步 —— 获取 API Key

完整体验需要**至少 2 把** Key（推荐 3 把）：

| 供应商 | 注册方式 | 核心模型 | 费用 |
|----------|---------|-----------|:----:|
| **DeepSeek**<br><sub>（或用 Anthropic）</sub> | [platform.deepseek.com](https://platform.deepseek.com/) → API Keys | deepseek-v4-pro | 按量 |
| **阿里云百炼 Qwen** | [dashscope.aliyun.com](https://dashscope.aliyun.com/) → 模型广场 → 开通 → API Key | qwen3-coder-plus<br>qwen-max<br>qwen-vl-max | 免费额度 |
| **智谱 AI GLM** | [open.bigmodel.cn](https://open.bigmodel.cn/) → API Keys | glm-4.5-air<br>glm-4.6v-flash | 免费额度 |
| **Google Gemini**<br><sub>（可选——四方会诊用）</sub> | [aistudio.google.com](https://aistudio.google.com/apikey) | gemini-3.5-flash | 免费额度 |
| **Suitui-AI**<br><sub>（可选——图像/视频生成）</sub> | [xskill.ai](https://www.xskill.ai/) | Seedance/Hailuo | 积分 |

> 💡 **不用 DeepSeek？** 删除 `settings.template.json` 中的 `ANTHROPIC_BASE_URL`，将 `ANTHROPIC_API_KEY` 指向 [Anthropic 控制台](https://console.anthropic.com/)。

### 第三步 —— 部署配置

```bash
cp settings.template.json ~/.claude/settings.json
cp CLAUDE.template.md   ~/.claude/CLAUDE.md
cp mcp.template.json    ~/.claude/.mcp.json
mkdir -p ~/.claude/scripts
cp scripts/*.py         ~/.claude/scripts/
```

### 第四步 —— 填入 Key

编辑 `~/.claude/settings.json`。将所有 `<YOUR_*_HERE>` 占位符替换为你的真实 Key。

### 第五步 —— 部署通行证锁

```bash
cp scripts/pre-commit.template .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### 第六步 —— 启动

```bash
claude
```

问一个技术问题（如"这个 for 循环怎么优化"）。如果终端出现 `Intent_Sniffer` YAML 块和 `🔗 [双引擎协同]` 日志，部署成功。

---

## 常见问题

<details>
<summary><b>Q: 可以只用 Qwen 不用 GLM 吗？</b></summary>
可以。不配置 <code>GLM_API_KEY</code> 即可。系统自动降级为 DS + Qwen 双引擎，日志会记录降级原因。
</details>

<details>
<summary><b>Q: 三方协同会增加多久等待时间？</b></summary>
通常 10-30 秒，取决于任务复杂度。简单问题自动走快速通道跳过协同。
</details>

<details>
<summary><b>Q: 日志文件在哪？占空间吗？</b></summary>
项目根目录下的 <code>./模型协同日志/</code>。每份约 1-2 KB，1000 份约 2 MB。
</details>

<details>
<summary><b>Q: 能绕过通行证锁吗？</b></summary>
不能。<code>Edit</code>/<code>Write</code> 操作被 PreToolUse Hook 拦截。<code>git commit</code> 被 pre-commit Hook 拦截。Bash 重定向写入会被 commit Hook 兜底捕获。
</details>

<details>
<summary><b>Q: V7.0 的量化数据采集是什么？</b></summary>
<code>CLAUDE.template.md</code> 中新增了 <code>程序员日志量化数据采集</code> 章节。配合 ActivityWatch + onefetch + git 自动采集时间分类、仓库快照、提交统计等量化指标，融合到每日日志中。详情见模板中的说明。
</details>

<details>
<summary><b>Q: GLM 质检门禁是什么？</b></summary>
V7.0 新增的 GLM 9.8+ 质量门禁：每次直写（配置文件修改、CLAUDE.md 变更等）必须先通过 GLM 质检评分。评分 ≥ 9.8 才能落地执行，确保每一行产出都经过第三方审查。
</details>

---

## 文件树

```
Model Federation V7.0/
├── README.md                     ← English
├── README_zh.md                  ← 中文（你在这里）
├── CLAUDE.template.md            (570+行) AI 行为规则模板（V7.0 新增量化采集 + GLM 门禁）
├── settings.template.json        (10把Key) 环境变量模板 — 全部占位符
├── mcp.template.json             (6个MCP) 服务器配置模板
└── scripts/
    ├── dashscope_router.py       (850+行) Qwen 全模型路由 + 通行证签发
    ├── glm_router.py             (360+行) GLM 全模型路由 + 通行证签发
    ├── vision_analyzer.py        (340+行) 并行双规视觉 (Qwen-VL + GLM-4.6V)
    ├── check_synergy_ticket.py   通行证锁 Hook (拦截 Edit/Write)
    └── pre-commit.template       Git Hook (拦截无证 commit)
```

---

## 完整工作流

```
用户："帮我审查这个函数"
    │
    ▼
[意图嗅探] → Domain: Coding, Need_Synergy: True
    │
    ▼
[Read] 提取真实源码（绝不发摘要）
    │
    ▼
[Payload] 写入 ~/.claude/temp/payload_*.txt（绕过命令行 8191 字符限制）
    │
    ▼
[Qwen] dashscope_router.py code --role "主刀医生" --ticket-for file.py
    │  → 生成优化补丁，签发 .claude/synergy_locks/file.py.ticket
    ▼
[GLM] glm_router.py semantic --role "质检护士"
    │  → 接收 Qwen 结果 + 原始代码，找出 Qwen 遗漏的边界问题
    ▼
[DeepSeek] 仲裁：逐条采纳/驳回
    │
    ▼
[物理举证] Read 日志文件，展示证据
    │
    ▼
[GC] 清理 temp/payload_*.txt
    │
    ▼
[用户] 收到唯一权威结论
```

---

## 量化数据采集流程（V7.0 新增）

```
ActivityWatch (时间追踪) ─┐
onefetch (仓库快照) ─────┤──→ collect_daily_data.ps1 ──→ daily_data_YYYYMMDD.json ──→ 日志归档
git log (提交统计) ──────┤
PSReadLine (终端历史) ───┘
```

采集脚本自动输出的数据直接融合到程序员日志的「变更记录」和「量化快照」字段。

---

## 更新日志

### V7.0 (2026-07-18)
- **程序员日志量化采集**：ActivityWatch 时间分类 + onefetch 仓库快照 + git 提交统计 + 终端历史自动归档
- **GLM 质检门禁**：文件直写前必须经 GLM 9.8+ 质检评分通过，确保每行产出经第三方审查
- **三方配置一致性检查**：CLAUDE.md / 记忆规则 / spec 模板三处日志字段定义一致性自动验证
- **CLAUDE.md JIT 路由表**：核心规则保留在 CLAUDE.md，详细规范按需加载 `.claude/spec/*.md`
- **八个日志字段强制序**：日期/会话起止/模型/Token消耗/花费反馈/变更记录/文件状态/量化快照
- **密钥遮蔽铁律**：日志中所有 API Key / Token / 密码自动 `***` 打码
- **前后端全链路测试**：6 个节点全部通过验证

### V6.0 (2026-06-22)
- **通行证锁**：物理文件系统拦截 Edit/Write/git-commit
- **开源发布**：完整模板包，零硬编码 Key，零路径泄露
- **Gemini 3.5 Flash**：确认部署，四方会诊专用
- **防作弊原码透传**：强制传递真实源码，禁止提纲式概括
- **技术仲裁权**：DeepSeek 评判 Qwen/GLM 输出，公开驳回错误建议
- **三步检查点**：杜绝长任务中跳过协同

### V5.x (2026-06-21—2026-06-22)
- 双路由脚本 (Qwen + GLM)，覆盖 14 种模型
- 物理日志铁律 (Log = Truth)
- 自主意图嗅探器取代关键词匹配
- 串行三方管线 (DS→Qwen→GLM→DS)

---

## 参与贡献

发现 Bug？有功能想法？提 Issue 或 PR。报告 Bug 时请包含：

- 操作系统和 Python 版本
- 准确的错误信息
- 复现步骤

欢迎 PR——尤其需要：
- 更多模型供应商接入
- Linux/macOS 通行证锁适配
- 安全加固

---

## 开源协议

MIT © Spiral
