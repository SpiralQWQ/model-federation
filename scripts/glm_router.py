#!/usr/bin/env python3
"""
智谱 AI (Zhipu GLM) 全量模型路由器 — 模型联邦系统组件
=====================================================
双引擎协同 (DeepSeek + DashScope) 的第三引擎：GLM 语义与边界专家。

路由规则：
  日常语义分析 / 轻量推理 → GLM-4.5-Air (128K, 免费额度)
  复杂推理 / 高质量文本     → GLM-4.7 (128K)
  快速响应 / 高并发         → GLM-4.7-Flash (128K)
  多模态视觉理解           → GLM-4.6V-Flash (免费视觉模型)

入口：
  python ~/.claude/scripts/glm_router.py <task_type> "<prompt>" [options]

环境变量：
  GLM_API_KEY — 智谱 AI API Key（从 settings.json env 注入）
"""

import json, os, sys, time, base64, io, urllib.request, urllib.error
from typing import Optional

# ═══════════════════════════════════════════════════════════
# 全局配置 — 全部从环境变量读取
# ═══════════════════════════════════════════════════════════
GLM_API_KEY = os.environ.get("GLM_API_KEY", "")
BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

if not GLM_API_KEY:
    print("[GLM] GLM_API_KEY 未设置！请在 settings.json env 中配置。", file=sys.stderr)
    # 不 exit，允许降级运行

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {GLM_API_KEY}"
}

# ═══════════════════════════════════════════════════════════
# 模型注册表
# ═══════════════════════════════════════════════════════════
MODEL_REGISTRY = {
    # ── 日常语义 / 轻量推理（免费额度，默认主力） ──
    "semantic": {
        "model": "glm-4.5-air",
        "context": "128K",
        "description": "日常语义分析、长尾边界提取、中文细腻度查漏",
        "endpoint": "/chat/completions",
        "max_tokens": 4096,
        "temperature": 0.3,
        "billing": "赠送额度内",
    },
    # ── 复杂推理 / 高质量文本 ──
    "reasoning": {
        "model": "glm-4.7",
        "context": "128K",
        "description": "复杂推理、语义逻辑一致性校验、逻辑盲区穿透",
        "endpoint": "/chat/completions",
        "max_tokens": 8192,
        "temperature": 0.2,
        "billing": "按量扣费",
    },
    # ── 快速响应 / 高并发 ──
    "fast": {
        "model": "glm-4.7-flash",
        "context": "128K",
        "description": "快速推理、轻量审查、高并发任务",
        "endpoint": "/chat/completions",
        "max_tokens": 4096,
        "temperature": 0.3,
        "billing": "按量扣费",
    },
    # ── 多模态视觉 ──
    "vision": {
        "model": "glm-4.6v-flash",
        "context": "多模态",
        "description": "免费视觉理解、OCR 识别、图片内容分析",
        "endpoint": "/chat/completions",
        "max_tokens": 2048,
        "temperature": 0.3,
        "billing": "免费模型",
    },
}


# ═══════════════════════════════════════════════════════════
# 图片编码（多模态用）
# ═══════════════════════════════════════════════════════════
def _encode_image(image_path: str, max_size: int = 2048) -> Optional[str]:
    """将图片编码为 base64，供 vision 模型使用。"""
    try:
        from PIL import Image
        img = Image.open(image_path)
        w, h = img.size
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except ImportError:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"[GLM] 图片编码失败: {e}", file=sys.stderr)
        return None


# ═══════════════════════════════════════════════════════════
# 🛡️ V4 物理日志 Hook — 防偷懒审计
# ═══════════════════════════════════════════════════════════

from datetime import datetime as _dt
import re as _re

SYNERGY_LOG_DIR = "模型协同日志"


def _ensure_log_dir() -> str:
    cwd = os.getcwd()
    log_dir = os.path.join(cwd, SYNERGY_LOG_DIR)
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def _next_log_number(log_dir: str) -> int:
    max_n = 0
    try:
        for name in os.listdir(log_dir):
            m = _re.match(r"^(\d{2,3})_", name)
            if m:
                max_n = max(max_n, int(m.group(1)))
    except Exception:
        pass
    return max_n + 1


def _write_physical_log(
    engine: str, model: str, task_type: str,
    prompt: str, response_text: str,
    input_tokens: int, output_tokens: int,
    elapsed: float, billing: str = "按量扣费", role: str = ""
) -> bool:
    try:
        log_dir = _ensure_log_dir()
        now_str = _dt.now().strftime("%Y%m%d-%H%M")

        seq = _next_log_number(log_dir)
        role_part = role.replace(" ", "") if role else task_type
        log_path = os.path.join(log_dir, f"{seq:02d}_{engine}({model})_{role_part}_{now_str}.md")
        prompt_short = prompt[:200].replace("\n", " ") + ("..." if len(prompt) > 200 else "")
        response_short = response_text[:300].replace("\n", " ") + ("..." if len(response_text) > 300 else "")
        timestamp = _dt.now().isoformat()

        entry = f"""# {engine}({model}) — {role or task_type}

| 字段 | 值 |
|------|-----|
| **引擎** | {engine} |
| **模型** | `{model}` |
| **任务类型** | {task_type} |
| **角色** | {role or '（路由自动调用）'} |
| **计费** | {billing} |
| **Token** | {input_tokens}→{output_tokens} |
| **耗时** | {elapsed:.1f}s |
| **时间** | {timestamp} |

**Prompt**: {prompt_short}

**响应**: {response_short}

---
"""
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(entry)
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception as e:
        print(f"[GLM] 物理日志写入失败: {e}", file=sys.stderr)
        return False


# ═══════════════════════════════════════════════════════════
# 核心调用函数
# ═══════════════════════════════════════════════════════════
def call_glm(task_type: str, prompt: str, **kwargs) -> dict:
    """
    GLM 模型调用入口。
    返回 {"text": "..."} 或 {"error": "..."}
    """
    if not GLM_API_KEY:
        return {"error": "GLM_API_KEY 未配置，GLM 引擎不可用"}

    config = MODEL_REGISTRY.get(task_type)
    if not config:
        return {
            "error": f"未知 GLM 任务类型: {task_type}",
            "available": list(MODEL_REGISTRY.keys())
        }

    model = config["model"]
    billing = config.get("billing", "按量扣费")

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"🧠 [GLM 联邦] 调用智谱专家: {model}", file=sys.stderr)
    print(f"🧠 [GLM 联邦] 任务类型: {task_type} — {config['description']}", file=sys.stderr)
    print(f"🧠 [GLM 联邦] 计费模式: {billing}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    start_time = time.time()

    # 构建 messages
    messages = [{"role": "user", "content": prompt}]

    # 多模态：图片支持
    image_path = kwargs.get("image_path")
    if image_path and os.path.exists(image_path):
        img_b64 = _encode_image(image_path)
        if img_b64:
            messages[0]["content"] = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            ]

    # 多模态：视频 URL 支持
    video_url = kwargs.get("video_url")
    if video_url:
        messages[0]["content"] = [
            {"type": "text", "text": prompt},
            {"type": "video_url", "video_url": {"url": video_url}}
        ]

    body = {
        "model": model,
        "messages": messages,
        "max_tokens": config.get("max_tokens", 4096),
        "temperature": config.get("temperature", 0.3),
    }

    # GLM-4.7 允许更高 max_tokens
    if "4.7" in model and "flash" not in model:
        body["max_tokens"] = min(kwargs.get("max_tokens", 8192), 8192)

    req = urllib.request.Request(
        f"{BASE_URL}{config['endpoint']}",
        data=json.dumps(body).encode("utf-8"),
        headers=HEADERS,
        method="POST"
    )

    elapsed = time.time() - start_time

    try:
        with urllib.request.urlopen(req, timeout=kwargs.get("timeout", 120)) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "choices" in result and result["choices"]:
                text = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})
                print(f"  [GLM] 耗时: {elapsed:.1f}s", file=sys.stderr)
                print(f"  [GLM] Token: {usage.get('prompt_tokens', 0)}→{usage.get('completion_tokens', 0)} "
                      f"({billing})", file=sys.stderr)
                # ── V4 物理日志 Hook ──
                log_ok = _write_physical_log(
                    engine="GLM", model=model, task_type=task_type,
                    prompt=prompt, response_text=text,
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0),
                    elapsed=elapsed, billing=billing,
                    role=kwargs.get("role", config.get("description", "")),
                )
                if not log_ok:
                    print("🛑 [GLM] 协同中断：偷懒审计未通过！", file=sys.stderr)
                return {"text": text, "model": model, "usage": usage, "billing": billing}
            else:
                return {"error": f"Unexpected: {json.dumps(result, indent=2)[:500]}"}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        return {"error": f"GLM API Error {e.code}: {body_text[:500]}"}
    except Exception as e:
        return {"error": f"GLM request failed: {str(e)}"}


def glm_vision_analyze(image_path: str, prompt: str) -> dict:
    """GLM 免费视觉模型分析（GLM-4.6V-Flash）。"""
    return call_glm("vision", prompt, image_path=image_path)


def glm_semantic_check(text: str, question: str = "") -> dict:
    """GLM 语义一致性校验与长尾边界提取。"""
    prompt = f"请对以下内容进行语义逻辑一致性校验，找出潜在逻辑盲区和长尾边界条件：\n\n{text}"
    if question:
        prompt += f"\n\n重点关注: {question}"
    return call_glm("semantic", prompt)


def glm_reasoning(task: str) -> dict:
    """GLM-4.7 复杂推理。"""
    return call_glm("reasoning", task)


# ═══════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print("智谱 GLM 全量模型路由器 — 模型联邦系统组件\n")
        print("用法: python ~/.claude/scripts/glm_router.py <task_type> <prompt> [options]\n")
        print("任务类型:")
        for t, c in MODEL_REGISTRY.items():
            print(f"  {t:<14} → {c['model']:<20} | {c['description']} ({c['billing']})")
        print("\n选项:")
        print("  --image <path>      图片路径（vision 任务）")
        print("  --video-url <url>   视频 URL（vision 任务）")
        print("  --role <角色名>      三方协同角色标注（如 主刀医生/质检护士）")
        print("  --prompt-file <path> 从文件读取长 Prompt（超长代码场景）")
        print("  --max-tokens <n>    最大输出 token 数")
        sys.exit(0)

    task_type = sys.argv[1]
    args = sys.argv[2:]
    prompt_parts = []
    kwargs = {}
    i = 0
    while i < len(args):
        if args[i] == "--image" and i + 1 < len(args):
            kwargs["image_path"] = args[i + 1]; i += 2
        elif args[i] == "--video-url" and i + 1 < len(args):
            kwargs["video_url"] = args[i + 1]; i += 2
        elif args[i] == "--prompt-file" and i + 1 < len(args):
            try:
                with open(args[i + 1], "r", encoding="utf-8") as pf:
                    prompt_parts.append(pf.read())
            except Exception as e:
                print(f"[GLM] 读取文件失败: {e}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--role" and i + 1 < len(args):
            kwargs["role"] = args[i + 1]; i += 2
        elif args[i] == "--max-tokens" and i + 1 < len(args):
            kwargs["max_tokens"] = int(args[i + 1]); i += 2
        else:
            prompt_parts.append(args[i]); i += 1

    prompt = " ".join(prompt_parts)
    if not prompt:
        print("[GLM] 请提供 prompt 参数", file=sys.stderr)
        sys.exit(1)

    result = call_glm(task_type, prompt, **kwargs)
    if "text" in result:
        print(result["text"])
    else:
        print(f"[GLM Error] {result.get('error', 'unknown')}", file=sys.stderr)
        sys.exit(1)
