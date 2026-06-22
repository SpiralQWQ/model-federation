<p align="center">
  <img src="cover_seedream.png" alt="Model Federation V6.0" width="800">
</p>

<p align="center">
  <a href="README_zh.md"><kbd>🇨🇳 中文</kbd></a> · <kbd>🇺🇸 English</kbd>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-6.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform">
</p>

<h1 align="center">Model Federation V6.0</h1>
<p align="center"><b>Local Multi-Model Federation Agent for Claude Code</b></p>

<p align="center">
  <i>DeepSeek orchestrates. Qwen performs surgery. GLM inspects. Gemini audits.<br>
  Four AI models. One airtight workflow. Zero unverified code commits.</i>
</p>

---

## What It Does

You're coding in Claude Code. You ask a question. Before any answer leaves your terminal, this system:

| Step | Action |
|:--:|------|
| 🔍 | **Sniffs** your intent — is this code? Architecture? A bug? Or just small talk? |
| 🧵 | **Extracts** real source code from your files (never sends summaries to models) |
| 🔧 | **Dispatches** Qwen to rewrite/optimize (the "Surgeon") |
| 🔬 | **Dispatches** GLM to find edge cases, deadlocks, and missing comments (the "Inspector") |
| ⚖️ | **Arbitrates** — DeepSeek judges both outputs, adopts what's right, rejects what's wrong |
| 📝 | **Logs** everything to physical Markdown files — immutable proof that review happened |
| 🎫 | **Issues a Ticket** — without it, Edit/Write/git-commit are physically blocked |

## Architecture

```
User Prompt
    │
    ▼
┌──────────────────────────────────────┐
│        Intent Sniffer (DeepSeek)       │
│   "Is this code? reasoning? vision?"  │
└──────────┬───────────────────────────┘
           │
    ┌──────▼──────┐     ┌──────────────┐     ┌─────────────┐
    │  Qwen        │ ──▶ │  GLM         │ ──▶ │  DeepSeek   │
    │  Surgeon     │     │  Inspector   │     │  Arbitrator │
    │  (qwen3-     │     │  (glm-4.5-air│     │  (v4-pro)   │
    │   coder-plus)│     │   / glm-4.7) │     │             │
    └──────┬───────┘     └──────┬───────┘     └──────┬──────┘
           │                    │                     │
           └────────────────────┴─────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Physical Log + Ticket │
                    │  (模型协同日志/*.md)    │
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

### Step 6 — Launch

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
<summary><b>Q: How do I verify it's working?</b></summary>
Ask a technical question. Look for: (1) <code>Intent_Sniffer</code> YAML, (2) <code>🔗</code> logs, (3) new <code>.md</code> files in 模型协同日志/.
</details>

---

## File Tree

```
Model Federation V6.0/
├── README.md                     ← English (you are here)
├── README_zh.md                  ← 中文
├── CLAUDE.template.md            (553 lines) Global AI behavior rules
├── settings.template.json        (10 keys)   Environment variables template
├── mcp.template.json             (6 servers) MCP configuration template
└── scripts/
    ├── dashscope_router.py       (850+ lines) Qwen full-model router + ticket issuer
    ├── glm_router.py             (360+ lines) GLM full-model router + ticket issuer
    ├── vision_analyzer.py        (340+ lines) Parallel dual-vision (Qwen-VL + GLM-4.6V)
    ├── check_synergy_ticket.py   Ticket Lock hook (PreToolUse — blocks Edit/Write)
    └── pre-commit.template       Git hook (blocks commit without ticket)
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

## Changelog

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
