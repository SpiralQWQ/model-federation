<p align="center">
  <img src="cover_seedream.png" alt="Model Federation V7.0" width="800">
</p>

<p align="center">
  <a href="README_zh.md"><kbd>🇨🇳 中文</kbd></a> · <kbd>🇺🇸 English</kbd>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-7.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform">
</p>

<h1 align="center">Model Federation V7.0</h1>
<p align="center"><b>Local Multi-Model Federation Agent for Claude Code</b></p>

<p align="center">
  <i>DeepSeek orchestrates. Qwen performs surgery. GLM inspects. Gemini audits.<br>
  Four AI models. One airtight workflow. Zero unverified code commits.</i>
</p>

---

## What It Does

This system transforms your Claude Code into a multi-model development team. It uses a **modular architecture** — core rules live in `CLAUDE.template.md` (~140 lines), detailed protocols in `spec/` directory loaded on demand via a Just-In-Time (JIT) routing table.

| Component | What It Does |
|:---------:|------|
| 🔍 | **Intent Sniffer** — classifies every query (code? reasoning? vision? chat?) |
| 🧵 | **JIT Routing Table** — loads detailed specs from `spec/` only when needed |
| 🔧 | **Qwen Surgeon** — code rewrite, optimization, syntax checking |
| 🔬 | **GLM Inspector** — edge cases, semantic check, quality gate (≥9.8/10) |
| ⚖️ | **DeepSeek Arbiter** — judges all outputs, adopts right, rejects wrong |
| 🔐 | **Gemini Auditor** — security scan & final compliance check (keyword "四方") |
| 🎫 | **Ticket Lock** — physical gate before Edit/Write/git-commit |
| 📊 | **Quantified Data** — ActivityWatch + onefetch + git stats → daily journal (pipeline by [dev-log-tool](https://github.com/SpiralQWQ/dev-log-tool)) |

## Architecture

```
User Prompt
    │
    ▼
┌──────────────────────────────────────┐
│      Intent Sniffer (DeepSeek)        │  ◀── core (~140 lines)
│  + JIT Routing Table → spec/*.md     │  ◀── loaded on demand
└──────────┬───────────────────────────┘
           │
    ┌──────▼──────┐     ┌──────────────┐     ┌─────────────┐
    │  Qwen        │ ──▶ │  GLM         │ ──▶ │  DeepSeek   │
    │  Surgeon     │     │  Inspector   │     │  Arbiter    │
    │  (qwen3-     │     │  (glm-4.5-air│     │  (v4-pro)   │
    │   coder-plus)│     │   / glm-4.7) │     │             │
    └──────┬───────┘     └──────┬───────┘     └──────┬──────┘
           │                    │                     │
           └────────────────────┴─────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Physical Log + Ticket │
                    │  + Quantified Data     │
                    └───────────────────────┘

Keyword "四方" ──▶ + Gemini 3.5 Flash (Security Auditor)
```

### Ticket Lock (The Physical Gate)

```
Before Edit/Write ──▶ check_synergy_ticket.py ──▶ No ticket? BLOCKED
Before git commit  ──▶ pre-commit hook          ──▶ No ticket? BLOCKED
After commit        ──▶ post-commit              ──▶ Tickets consumed
```

This is not a "please remember" rule. It's operating-system-level enforcement.

---

## Installation

### Prerequisites

| Requirement | Minimum | Check |
|------------|:-------:|-------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| Claude Code | latest | `claude --version` |
| OS | Windows 10+ / macOS 12+ / Ubuntu 20.04+ | — |

> ℹ️ Zero third-party Python dependencies. All router scripts use only stdlib. Optional: `Pillow` for image resizing in vision_analyzer.

### Step 1 — Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

### Step 2 — Get API Keys

You need **at least 2 keys** for the full experience (3 recommended):

| Provider | Sign Up | Key Models | Cost |
|----------|---------|-----------|:----:|
| **DeepSeek**<br><sub>(or Anthropic)</sub> | [platform.deepseek.com](https://platform.deepseek.com/) → API Keys | deepseek-v4-pro | Pay-per-use |
| **Qwen (Alibaba)** | [dashscope.aliyun.com](https://dashscope.aliyun.com/) → API Key | qwen3-coder-plus<br>qwen-max<br>qwen-vl-max | Free tier |
| **GLM (Zhipu)** | [open.bigmodel.cn](https://open.bigmodel.cn/) → API Keys | glm-4.5-air<br>glm-4.6v-flash | Free tier |
| **Gemini**<br><sub>(optional)</sub> | [aistudio.google.com](https://aistudio.google.com/apikey) | gemini-3.5-flash | Free tier |
| **Suitui-AI**<br><sub>(optional)</sub> | [xskill.ai](https://www.xskill.ai/) | Seedance/Hailuo | Credits |

> 💡 **Not using DeepSeek?** Delete `ANTHROPIC_BASE_URL` in `settings.template.json` and point `ANTHROPIC_API_KEY` to [Anthropic's Console](https://console.anthropic.com/).

### Step 3 — Deploy Configs

```bash
cp settings.template.json ~/.claude/settings.json
cp CLAUDE.template.md   ~/.claude/CLAUDE.md
cp mcp.template.json    ~/.claude/.mcp.json
mkdir -p ~/.claude/scripts
cp scripts/*.py         ~/.claude/scripts/
```

### Step 4 — Fill In Your Keys

Edit `~/.claude/settings.json`. Replace every `<YOUR_*_HERE>` placeholder.

### Step 5 — Deploy Ticket Lock

```bash
cp scripts/pre-commit.template .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Step 6 — (V7.0) Deploy Spec Directory

Copy `spec/` to your project root (required for JIT routing table):

```bash
cp -r spec/ /path/to/your/project/spec/
```

> Without `spec/`, multi-model arbitration and quality gates fall back to inline defaults.

### Step 7 — Launch

```bash
claude
```

Ask a technical question. If you see an `Intent_Sniffer` YAML block and `🔗` logs, you're live.

---

## FAQ

<details>
<summary><b>Q: Can I use only Qwen without GLM?</b></summary>
Yes. The system auto-degrades to DS+Qwen dual-mode and logs the degradation.
</details>

<details>
<summary><b>Q: How much latency does tri-party add?</b></summary>
10–30 seconds. Simple queries take the fast lane and skip synergy entirely.
</details>

<details>
<summary><b>Q: Where are the log files?</b></summary>
<code>./模型协同日志/</code> in your project root. ~1–2 KB each, 1,000 entries ≈ 2 MB.
</details>

<details>
<summary><b>Q: Can I bypass the ticket lock?</b></summary>
No. <code>Edit</code>/<code>Write</code> on source files are intercepted by a PreToolUse hook. <code>git commit</code> is intercepted by a pre-commit hook. Raw Bash redirects are caught by the commit hook.
</details>

<details>
<summary><b>Q: What is the quantified data collection in V7.0?</b></summary>
Provided by the companion repo <a href="https://github.com/SpiralQWQ/dev-log-tool"><b>dev-log-tool</b></a> (<a href="https://gitee.com/Spiral_QWQ/dev-log-tool">Gitee mirror</a>). It includes <code>collect/collect_daily_data.ps1</code> (ActivityWatch + onefetch + git + PSReadLine) and log templates (spec/log_templates.md). See its README for details.
</details>

<details>
<summary><b>Q: What is the GLM quality gate?</b></summary>
V7.0's new GLM quality gate: before any file write (config changes, CLAUDE.md edits, etc.), the output must pass a GLM quality check with score ≥ 9.8/10. Every line of output is third-party verified before landing.
</details>

---

## File Tree

```
model-federation/
├── README.md                     ← English (you are here)
├── README_zh.md                  ← 中文
├── CLAUDE.template.md            (~140 lines) Core rules + JIT routing table (V7.0: modular)
├── settings.template.json        (10 keys)    Env var template — all placeholders
├── mcp.template.json             (6 servers)  MCP configuration template
├── scripts/
│   ├── dashscope_router.py       (850+ lines) Qwen full-model router + ticket issuer
│   ├── glm_router.py             (360+ lines) GLM full-model router + ticket issuer
│   ├── vision_analyzer.py        (340+ lines) Parallel dual-vision (Qwen-VL + GLM-4.6V)
│   ├── check_synergy_ticket.py   Ticket Lock hook (PreToolUse — blocks Edit/Write)
│   └── pre-commit.template       Git hook (blocks commit without ticket)
└── spec/                         ⬅ V7.0 Modular specs, loaded by JIT routing table
    ├── collaboration.md          Tri-party / four-party protocols
    ├── code_review.md            Pre-submit checklist
    ├── vision_rules.md           Dual vision analysis rules
    ├── billing_rules.md          Token billing categories & report format
    ├── superpowers.md            Superpowers skill inventory
    └── log_templates.md          Log naming & content requirements
```

---

## Workflow (End to End)

```
User: "review this function"
    │
    ▼
[Intent Sniffer] → Domain: Coding, Need_Synergy: True
    │
    ▼
[Read] Extract real source code (never summarized)
    │
    ▼
[Payload] Write to temp file (bypasses CMD 8191-char limit)
    │
    ▼
[Qwen] dashscope_router.py code --role "Surgeon" --ticket-for file.py
    │  → Generates optimization patch, issues .claude/synergy_locks/file.py.ticket
    ▼
[GLM] glm_router.py semantic --role "Inspector"
    │  → Receives Qwen's output + original code, finds edge cases Qwen missed
    ▼
[DeepSeek] Arbitrate: adopt/reject each suggestion
    │
    ▼
[Physical Evidence] Read log files, display proof
    │
    ▼
[GC] Clean temp files
    │
    ▼
[User] Receives single authoritative conclusion
```

---

## Quantified Data Pipeline (V7.0 NEW)

Quantified data collection is provided by the **companion repo** — model-federation focuses on model routing and collaboration, while `dev-log-tool` handles journal archiving + data collection:

| Repo | GitHub | Gitee | Role |
|------|--------|-------|------|
| **model-federation** | [SpiralQWQ/model-federation](https://github.com/SpiralQWQ/model-federation) | [Spiral_QWQ/model-federation](https://gitee.com/Spiral_QWQ/model-federation) | Model routing, Ticket Lock, spec/ |
| **dev-log-tool** | [SpiralQWQ/dev-log-tool](https://github.com/SpiralQWQ/dev-log-tool) | [Spiral_QWQ/dev-log-tool](https://gitee.com/Spiral_QWQ/dev-log-tool) | Log templates, collection scripts, workflow |

```
ActivityWatch (time tracking) ──┐
onefetch (repo snapshot) ───────┤──→ dev-log-tool/collect/collect_daily_data.ps1 ──→ daily_data.json ──→ journal
git log (commit stats) ─────────┤
PSReadLine (terminal history) ──┘
```

Both repos are independently published but designed to work together. After deploying model-federation, also pull dev-log-tool for the complete logging workflow.

---

## Changelog

### V7.0 (2026-07-18)
- **Architecture overhaul**: 627-line monolithic template → ~140-line core rules + JIT routing table + `spec/` modular directory (6 files)
- **GLM quality gate**: File writes require GLM quality score ≥ 9.8/10 — every output is third-party verified
- **Quantified data pipeline**: ActivityWatch time categories + onefetch repo snapshots + git commit stats + terminal history auto-archived
- **Key masking mandate**: All API Keys / Tokens / passwords auto-redacted with `***` in logs
- **3-way config consistency check**: Auto-verify CLAUDE.md / memory rules / spec template alignment

### V6.0 (2026-06-22)
- **Ticket Lock**: Physical file-system gate blocks Edit/Write/git-commit without synergy
- **Open Source Release**: Full template package with zero hardcoded keys or paths
- **Gemini 3.5 Flash**: Confirmed and deployed for four-party consultations
- **Anti-Cheat Payload**: Raw code passthrough mandatory — no more sending summaries to models
- **Technical Arbitration**: DeepSeek judges Qwen/GLM output, rejects bad advice publicly
- **Three-Gate Checkpoint**: Prevents skipping synergy on long multi-step tasks

### V5.x (2026-06-21—2026-06-22)
- Dual router scripts (Qwen + GLM) with 14 model types
- Physical log mandate (Log = Truth)
- Autonomous Intent Sniffer replacing keyword matching
- Serial 3-party pipeline (DS→Qwen→GLM→DS)

---

## Contributing

Found a bug? Have a feature idea? Open an issue or PR. Include:

- Your OS and Python version
- Exact error message or unexpected behavior
- Steps to reproduce

PRs welcome — especially for:
- Additional model provider integrations
- Platform-specific hook implementations
- Security hardening

---

## License

MIT © Spiral
