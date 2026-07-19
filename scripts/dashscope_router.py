#!/usr/bin/env python3
"""
DashScope (阿里云百炼) 全量模型路由器 — 双引擎协同中枢
========================================================
DeepSeek (决策脑) + DashScope (领域专家) 协同工作流。

路由规则：
  推理/决策 → qwen-max (32K)
  代码生成/重构/Bug修复 → qwen3-coder-plus (128K)
  千万字长文本/跨文档分析 → qwen-long
  视频理解/监控分析 → qwen3-vl-plus
  图片分析/图表理解 → qwen-vl-max (默认)
  图像生成 → wan2.7-image-pro

用法：
  python tools/dashscope_router.py <task_type> <prompt_or_path> [options]

示例：
  python tools/dashscope_router.py code "写一个快速排序的Python实现"
  python tools/dashscope_router.py long_text "总结这些文档..." --files a.pdf b.docx
  python tools/dashscope_router.py image_gen "赛博朋克城市夜景" --size 1024x1024
  python tools/dashscope_router.py video_understanding ./video.mp4 "总结视频内容"
"""

import json
import os
import sys
import time
import base64
import urllib.request
import urllib.error
from typing import Optional

# ============================================================
# 全局配置 — 全部从环境变量读取
# ============================================================
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
# 图像/视频生成用原生 DashScope API
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/api/v1"

if not QWEN_API_KEY:
    print("❌ QWEN_API_KEY 未设置！请在 settings.json env 中配置。", file=sys.stderr)
    sys.exit(1)

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {QWEN_API_KEY}"
}

# ============================================================
# 模型注册表：按任务类型路由
# ============================================================
MODEL_REGISTRY = {
    # ── 推理与决策 ──
    "reasoning": {
        "model": "qwen-max",
        "context": "32K",
        "description": "复杂推理、数学推演、架构设计、策略决策",
        "endpoint": "/chat/completions",
        "max_tokens": 4096,
        "temperature": 0.2,
    },
    "decision": {
        "model": "qwen-max",
        "context": "32K",
        "description": "多方案对比、最终决策、风险评估",
        "endpoint": "/chat/completions",
        "max_tokens": 4096,
        "temperature": 0.1,
    },
    # ── 代码生成 ──
    "code": {
        "model": "qwen3-coder-plus",
        "context": "128K",
        "description": "代码生成、重构、Bug修复、单元测试编写",
        "endpoint": "/chat/completions",
        "max_tokens": 8192,
        "temperature": 0.1,
    },
    "code_review": {
        "model": "qwen3-coder-plus",
        "context": "128K",
        "description": "代码审查、安全审计、性能分析",
        "endpoint": "/chat/completions",
        "max_tokens": 4096,
        "temperature": 0.1,
    },
    # ── 长文本分析 ──
    "long_text": {
        "model": "qwen-long",
        "context": "10M tokens",
        "description": "千万字长文本摘要、跨文档分析、大海捞针",
        "endpoint": "/chat/completions",
        "max_tokens": 8192,
        "temperature": 0.3,
    },
    # ── 视频理解 ──
    "video_understanding": {
        "model": "qwen3-vl-plus",
        "context": "多模态",
        "description": "视频内容理解、监控分析、会议录像总结",
        "endpoint": "/chat/completions",
        "max_tokens": 4096,
        "temperature": 0.3,
    },
    # ── 图片分析 ──
    "image_analysis": {
        "model": "qwen-vl-max",
        "context": "多模态",
        "description": "图片内容识别、图表理解、OCR",
        "endpoint": "/chat/completions",
        "max_tokens": 2048,
        "temperature": 0.3,
    },
    # ── 图像生成 ──
    "image_gen": {
        "model": "wan2.7-image-pro",
        "context": "N/A",
        "description": "文生图 — 中文语义理解强，物理光影准确",
        "endpoint": "/services/aigc/text2image/image-synthesis",
        "api_type": "dashscope_native",  # 原生 DashScope API（非 OpenAI 兼容）
    },
    # ── 视频生成（当前 Key 无可用视频模型，作为占位）
    "video_gen_t2v": {
        "model": "wan2.7-image-pro",
        "context": "N/A",
        "description": "文生视频 — 当前 Key 暂未开通，请使用 suitui-ai Seedance/Hailuo",
        "endpoint": "/services/aigc/text2video/video-synthesis",
        "api_type": "dashscope_native",
        "unavailable": True,
    },
    "video_gen_i2v": {
        "model": "wan2.7-image-pro",
        "context": "N/A",
        "description": "图生视频 — 当前 Key 暂未开通，请使用 suitui-ai Seedance/Hailuo",
        "endpoint": "/services/aigc/image2video/video-synthesis",
        "api_type": "dashscope_native",
        "unavailable": True,
    },
}

# ============================================================
# 冲突模型对比表（生图/生视频时展示）
# ============================================================
CONFLICT_COMPARISON = {
    "image_gen": """
╔══════════════════════════════════════════════════════════════╗
║              🎨 图像生成 — 多平台模型对比                      ║
╠═══════════════╦══════════╦══════════╦══════════╦═══════════╣
║ 特性           ║ Wan2.7   ║ Seedream ║ Flux 2   ║ GPT Img2  ║
║               ║ ImagePro ║ 4.5      ║ Flash    ║           ║
╠═══════════════╬══════════╬══════════╬══════════╬═══════════╣
║ 中文语义遵循    ║ ★★★★★    ║ ★★★★     ║ ★★★      ║ ★★★★      ║
║ 物理光影准确度   ║ ★★★★     ║ ★★★★★    ║ ★★★★     ║ ★★★★      ║
║ 文字渲染        ║ ★★★★     ║ ★★★★     ║ ★★★★★    ║ ★★★★★     ║
║ 写实风格        ║ ★★★★     ║ ★★★★★    ║ ★★★★     ║ ★★★★      ║
║ 艺术风格        ║ ★★★      ║ ★★★★     ║ ★★★★     ║ ★★★★      ║
║ 生成速度        ║ 中       ║ 慢       ║ 极速     ║ 中        ║
║ 费用            ║ 百炼免费  ║ 2积分     ║ 2积分    ║ 按量付费   ║
╚═══════════════╩══════════╩══════════╩══════════╩═══════════╝
注: 视频生成模型当前 Key 暂未开通，建议使用 suitui-ai 的 Seedance/Hailuo。""",
    "video_gen": """
╔══════════════════════════════════════════════════════════════╗
║              🎬 视频生成 — 多平台模型对比                      ║
╠═══════════════╦══════════╦══════════╦══════════╦═══════════╣
║ 特性           ║ 百炼Wan  ║ Seedance ║ Hailuo   ║ Kling O3  ║
║               ║ (暂未开通)║ 2.0      ║ 2.3      ║           ║
╠═══════════════╬══════════╬══════════╬══════════╬═══════════╣
║ 中文语义遵循    ║ ★★★★★    ║ ★★★★     ║ ★★★      ║ ★★★       ║
║ 物理模拟        ║ ★★★★★    ║ ★★★★     ║ ★★★★     ║ ★★★★      ║
║ 人物一致性      ║ ★★★★     ║ ★★★★★    ║ ★★★      ║ ★★★★      ║
║ 音频生成        ║ ★★★      ║ ★★★★     ║ N/A      ║ N/A       ║
║ 生成速度        ║ 慢       ║ 中       ║ 快       ║ 中        ║
║ 费用            ║ 百炼免费  ║ 积分     ║ 积分     ║ 积分      ║
╚═══════════════╩══════════╩══════════╩══════════╩═══════════╝
""",
}


# ============================================================
# 🛡️ V4 物理日志 Hook — 防偷懒审计（协同中断判定标准）
# ============================================================

from datetime import datetime as _dt
import re as _re

SYNERGY_LOG_DIR = "模型协同日志"


def _ensure_log_dir() -> str:
    """确保当前工作根目录下存在 模型日志/ 目录，返回绝对路径。"""
    cwd = os.getcwd()
    log_dir = os.path.join(cwd, SYNERGY_LOG_DIR)
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def _next_log_number(log_dir: str) -> int:
    """扫描目录中已有日志的最大编号，返回下一个可用编号。"""
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
    engine: str,
    model: str,
    task_type: str,
    prompt: str,
    response_text: str,
    input_tokens: int,
    output_tokens: int,
    elapsed: float,
    billing: str = "按量扣费",
    role: str = ""
) -> bool:
    """
    向 ./模型日志/协同日志_YYYYMMDD.md 追加一条协同记录。
    返回 True 表示写入成功；False 表示写入失败（触发偷懒审计中断）。

    这是 V4 防偷懒物理卡点：若此函数返回 False，上层必须中断并报错。
    """
    try:
        log_dir = _ensure_log_dir()
        now_str = _dt.now().strftime("%Y%m%d-%H%M")
        timestamp = _dt.now().isoformat()

        # 每条协同调用生成独立文件（精确到分钟）
        seq = _next_log_number(log_dir)
        role_part = role.replace(" ", "") if role else task_type
        log_path = os.path.join(log_dir, f"{seq:02d}_{engine}({model})_{role_part}_{now_str}.md")

        # 截断过长文本
        prompt_short = prompt[:200].replace("\n", " ") + ("..." if len(prompt) > 200 else "")
        response_short = response_text[:300].replace("\n", " ") + ("..." if len(response_text) > 300 else "")

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

---"""

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(entry)
            f.flush()
            os.fsync(f.fileno())

        return True
    except Exception as e:
        print(f"❌ [物理日志写入失败] {e}", file=sys.stderr)
        return False


# ============================================================
# 核心函数
# ============================================================

def call_dashscope(task_type: str, prompt: str, **kwargs) -> dict:
    """
    双引擎协同入口：
    1. 打印 [双引擎协同] 日志
    2. 调用对应的百炼专家模型
    3. 输出 [模型调用统计]
    """
    config = MODEL_REGISTRY.get(task_type)
    if not config:
        return {
            "error": f"未知任务类型: {task_type}",
            "available": list(MODEL_REGISTRY.keys())
        }

    model = config["model"]
    api_type = config.get("api_type", "openai_compatible")

    # ── 双引擎协同日志 ──
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"🔗 [双引擎协同] DeepSeek (决策脑) 已完成任务拆解", file=sys.stderr)
    print(f"🔗 [双引擎协同] 现调用百炼专家模型: {model}", file=sys.stderr)
    print(f"🔗 [双引擎协同] 任务类型: {task_type} — {config['description']}", file=sys.stderr)
    print(f"🔗 [双引擎协同] 上下文窗口: {config['context']}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    start_time = time.time()

    if api_type == "dashscope_native":
        result = _call_dashscope_native(config, prompt, **kwargs)
    else:
        result = _call_openai_compatible(config, prompt, **kwargs)

    elapsed = time.time() - start_time

    # ── 计费播报 ──
    usage = result.get("usage", {})
    input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
    output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))
    total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

    print(f"\n{'─'*60}", file=sys.stderr)
    print(f"📊 [模型调用统计]", file=sys.stderr)
    print(f"  触发模型: {model}", file=sys.stderr)
    print(f"  参与引擎: DeepSeek (规划/分析) + {model} (执行/验证)", file=sys.stderr)
    print(f"  消耗 Token: {input_tokens} (输入) + {output_tokens} (输出) = {total_tokens}", file=sys.stderr)
    print(f"  耗时: {elapsed:.1f}s", file=sys.stderr)
    if "estimated_cost" in result:
        print(f"  预估计费: {result['estimated_cost']}", file=sys.stderr)
    print(f"  (提示: 若免费额度用尽，将产生实际费用)", file=sys.stderr)
    print(f"{'─'*60}\n", file=sys.stderr)

    # ── V4 物理日志 Hook ──
    if "text" in result:
        log_ok = _write_physical_log(
            engine="Qwen",
            model=model,
            task_type=task_type,
            prompt=prompt,
            response_text=result["text"],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            elapsed=elapsed,
            billing="百炼免费额度" if task_type in ("image_analysis", "image_gen") else "按量扣费",
            role=kwargs.get("role", config.get("description", "")),
        )
        if not log_ok:
            print("🛑 协同中断：偷懒审计未通过！物理日志写入失败。", file=sys.stderr)

    return result


def _call_openai_compatible(config: dict, prompt: str, **kwargs) -> dict:
    """OpenAI 兼容接口调用（qwen-max / qwen-coder / qwen-long / qwen-vl）"""
    model = config["model"]

    # 构建 messages
    messages = [{"role": "user", "content": prompt}]

    # 多模态支持：图片（base64 内联）
    image_path = kwargs.get("image_path")
    if image_path and os.path.exists(image_path) and not _is_video_file(image_path):
        img_b64 = _encode_image(image_path)
        if img_b64:
            messages[0]["content"] = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            ]

    # 多模态支持：视频（本地文件 → OSS 上传 → 公网 URL）
    if image_path and os.path.exists(image_path) and _is_video_file(image_path):
        video_url = _resolve_video_url(image_path)
        messages[0]["content"] = [
            {"type": "text", "text": prompt},
            {"type": "video_url", "video_url": {"url": video_url}}
        ]

    # 长文本：如果传入 files，拼接文件内容
    files = kwargs.get("files", [])
    if files:
        file_contents = []
        for fp in files:
            if os.path.exists(fp):
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        file_contents.append(f"--- {fp} ---\n{f.read()}")
                except Exception:
                    file_contents.append(f"--- {fp} ---\n[二进制文件，跳过文本读取]")
        if file_contents:
            combined = "\n\n".join(file_contents)
            messages[0]["content"] = f"以下是要分析的文档内容:\n\n{combined}\n\n用户问题: {prompt}"

    body = {
        "model": model,
        "messages": messages,
        "max_tokens": config.get("max_tokens", 4096),
        "temperature": config.get("temperature", 0.2),
    }

    # qwen-long 特殊参数
    if model == "qwen-long":
        body["temperature"] = 0.3
        body["presence_penalty"] = 0.1

    # qwen-coder 特殊参数
    if "coder" in model:
        body["temperature"] = 0.1
        body["top_p"] = 0.95

    req = urllib.request.Request(
        f"{BASE_URL}{config['endpoint']}",
        data=json.dumps(body).encode("utf-8"),
        headers=HEADERS,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=kwargs.get("timeout", 120)) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "choices" in result and result["choices"]:
                return {
                    "text": result["choices"][0]["message"]["content"],
                    "model": model,
                    "usage": result.get("usage", {}),
                }
            else:
                return {"error": f"Unexpected: {json.dumps(result, indent=2)[:500]}"}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return {"error": f"API Error {e.code}: {body[:500]}"}
    except Exception as e:
        return {"error": str(e)}


def _call_dashscope_native(config: dict, prompt: str, **kwargs) -> dict:
    """
    原生 DashScope API 调用（图像/视频生成）
    注意：这些是异步 API，提交后返回 task_id，需轮询
    """
    model = config["model"]
    endpoint = config["endpoint"]

    body = {
        "model": model,
        "input": {"prompt": prompt},
        "parameters": {}
    }

    # 图像生成参数
    if "t2i" in model:
        size = kwargs.get("size", "1024*1024")
        body["input"]["negative_prompt"] = kwargs.get("negative_prompt", "")
        body["parameters"] = {
            "size": size,
            "n": kwargs.get("n", 1),
        }
        if "seed" in kwargs:
            body["parameters"]["seed"] = kwargs["seed"]

    # 视频生成参数
    if "t2v" in model or "i2v" in model:
        if kwargs.get("image_url"):
            body["input"]["image_url"] = kwargs["image_url"]
        duration = kwargs.get("duration", 5)
        body["parameters"]["duration"] = duration

    req = urllib.request.Request(
        f"{DASHSCOPE_API_URL}{endpoint}",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {QWEN_API_KEY}",
            "X-DashScope-Async": "enable"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            task_id = result.get("output", {}).get("task_id", "")
            status = result.get("output", {}).get("task_status", "UNKNOWN")
            return {
                "task_id": task_id,
                "status": status,
                "model": model,
                "note": "任务已提交。请使用 get_dashscope_result(task_id) 查询结果",
                "usage": result.get("usage", {}),
            }
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8")
        return {"error": f"API Error {e.code}: {body_text[:500]}"}
    except Exception as e:
        return {"error": str(e)}


def get_dashscope_result(task_id: str, task_type: str = "image_gen") -> dict:
    """查询异步任务结果（图像/视频生成）"""
    config = MODEL_REGISTRY.get(task_type, MODEL_REGISTRY["image_gen"])
    model = config["model"]

    # DashScope 异步任务查询端点
    endpoint_map = {
        "wan2.7-image-pro": "/services/aigc/text2image/image-synthesis",
        "qwen-image-2.0-pro": "/services/aigc/text2image/image-synthesis",
    }
    endpoint = endpoint_map.get(model, endpoint_map["wan2.7-image-pro"])

    req = urllib.request.Request(
        f"{DASHSCOPE_API_URL}{endpoint}/{task_id}",
        headers={
            "Authorization": f"Bearer {QWEN_API_KEY}",
        },
        method="GET"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def show_conflict_comparison(task_type: str) -> str:
    """展示冲突模型对比表（生图/生视频时调用）"""
    if task_type in ("image_gen", "image"):
        return CONFLICT_COMPARISON["image_gen"]
    elif task_type in ("video_gen", "video_gen_t2v", "video_gen_i2v", "video"):
        return CONFLICT_COMPARISON["video_gen"]
    return ""


# ============================================================
# 双引擎协同工作流 API
# ============================================================

def synergy_execute(task_type: str, prompt: str, **kwargs) -> str:
    """
    双引擎协同执行 — 高层 API
    ============================

    流程：
    1. DeepSeek 拆解任务（本函数的调用者已做）
    2. 路由到百炼专家模型
    3. 返回专家结果给 DeepSeek 做二次评估

    返回：专家模型的文本输出（或生成任务的 task_id）
    """
    result = call_dashscope(task_type, prompt, **kwargs)

    if "error" in result:
        return f"❌ 百炼专家调用失败: {result['error']}"

    if "task_id" in result:
        return f"✅ 任务已提交: {result['task_id']}\n   模型: {result['model']}\n   {result['note']}"

    if "text" in result:
        return result["text"]

    return json.dumps(result, indent=2, ensure_ascii=False)


def list_available_models() -> list:
    """列出所有可用的百炼模型及其任务类型"""
    models = []
    for task_type, config in MODEL_REGISTRY.items():
        models.append({
            "task_type": task_type,
            "model": config["model"],
            "context": config["context"],
            "description": config["description"],
        })
    return models


# ============================================================
# 视频文件上传（OSS）— Qwen-VL 视频理解需要公网 URL
# ============================================================

import hmac
import hashlib
import email.utils
import uuid

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".3gp"}
MAX_VIDEO_SIZE_MB = 500  # 单文件上限 500MB


def _is_video_file(path: str) -> bool:
    """判断文件是否为视频（按扩展名）。"""
    return os.path.splitext(path)[1].lower() in VIDEO_EXTENSIONS


def _upload_to_oss(local_path: str) -> str:
    """
    上传本地视频到阿里云 OSS，返回公网访问 URL。

    使用 HMAC-SHA1 签名，零外部依赖。
    所需环境变量（缺一不可）：
      OSS_ACCESS_KEY_ID     — 阿里云 AccessKey ID
      OSS_ACCESS_KEY_SECRET — 阿里云 AccessKey Secret
      OSS_BUCKET_NAME       — OSS Bucket 名称
      OSS_ENDPOINT          — OSS 地域节点，如 oss-cn-hangzhou.aliyuncs.com
    """
    access_key_id = os.environ.get("OSS_ACCESS_KEY_ID", "")
    access_key_secret = os.environ.get("OSS_ACCESS_KEY_SECRET", "")
    bucket = os.environ.get("OSS_BUCKET_NAME", "")
    endpoint = os.environ.get("OSS_ENDPOINT", "")

    if not all([access_key_id, access_key_secret, bucket, endpoint]):
        raise RuntimeError(
            "OSS 凭证未配置。请设置 4 个环境变量:\n"
            "  OSS_ACCESS_KEY_ID\n"
            "  OSS_ACCESS_KEY_SECRET\n"
            "  OSS_BUCKET_NAME\n"
            "  OSS_ENDPOINT (如 oss-cn-hangzhou.aliyuncs.com)\n\n"
            "获取方式: 阿里云控制台 → 对象存储 OSS → Bucket 列表 → 创建 Bucket\n"
            "或直接提供视频的公网 URL 作为 --image 参数。"
        )

    # 生成唯一对象名
    ext = os.path.splitext(local_path)[1].lower()
    object_name = f"dashscope-videos/{uuid.uuid4().hex}{ext}"
    host = f"{bucket}.{endpoint}"
    url = f"https://{host}/{object_name}"

    # 检查文件大小
    file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
    if file_size_mb > MAX_VIDEO_SIZE_MB:
        raise RuntimeError(
            f"视频文件 {file_size_mb:.0f}MB 超过上限 {MAX_VIDEO_SIZE_MB}MB，"
            f"请压缩后再试或提供公网 URL。"
        )
    print(f"  📤 上传视频到 OSS ({file_size_mb:.1f}MB)...", file=sys.stderr)

    with open(local_path, "rb") as f:
        file_data = f.read()

    # MIME 类型映射
    mime_map = {
        ".mp4": "video/mp4", ".mov": "video/quicktime",
        ".avi": "video/x-msvideo", ".mkv": "video/x-matroska",
        ".webm": "video/webm", ".flv": "video/x-flv",
        ".wmv": "video/x-ms-wmv", ".3gp": "video/3gpp",
    }
    content_type = mime_map.get(ext, "application/octet-stream")

    # HMAC-SHA1 签名（RFC 2104 + OSS Header 签名规范）
    date_str = email.utils.formatdate(usegmt=True)
    # CanonicalizedResource: /{bucket}/{object_name}
    # CanonicalizedOSSHeaders: x-oss-object-acl:public-read\n
    string_to_sign = (
        f"PUT\n"                          # VERB
        f"\n"                              # Content-MD5 (empty)
        f"{content_type}\n"               # Content-Type
        f"{date_str}\n"                   # Date
        f"x-oss-object-acl:public-read\n" # CanonicalizedOSSHeaders
        f"/{bucket}/{object_name}"        # CanonicalizedResource
    )
    signature = base64.b64encode(
        hmac.new(
            access_key_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("utf-8")

    headers = {
        "Authorization": f"OSS {access_key_id}:{signature}",
        "Date": date_str,
        "Content-Type": content_type,
        "x-oss-object-acl": "public-read",
    }

    req = urllib.request.Request(url, data=file_data, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            if resp.status == 200:
                print(f"  ✅ 上传成功: {url}", file=sys.stderr)
                return url
            else:
                raise RuntimeError(f"OSS 上传返回 HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OSS 上传失败 HTTP {e.code}: {body_text[:300]}")


def _resolve_video_url(path_or_url: str) -> str:
    """
    解析视频地址：
    - 如果是 http/https URL → 直接返回
    - 如果是本地文件 → 校验格式后上传 OSS，返回公网 URL
    """
    if path_or_url.startswith(("http://", "https://")):
        print(f"  🔗 使用公网视频 URL: {path_or_url[:80]}...", file=sys.stderr)
        return path_or_url

    if not os.path.exists(path_or_url):
        raise FileNotFoundError(f"视频文件不存在: {path_or_url}")

    if not _is_video_file(path_or_url):
        raise ValueError(
            f"不支持的视频格式: {os.path.splitext(path_or_url)[1] or '<none>'}。"
            f"支持: {', '.join(sorted(VIDEO_EXTENSIONS))}"
        )

    return _upload_to_oss(path_or_url)


def encode_image(image_path: str, max_size: int = 2048) -> Optional[str]:
    """将图片编码为 base64，供多模态调用使用"""
    try:
        from PIL import Image
        img = Image.open(image_path)
        w, h = img.size
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except ImportError:
        # 无 PIL 时直接读文件
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"⚠ 图片编码失败: {e}", file=sys.stderr)
        return None


# 导出供外部调用
_encode_image = encode_image


# ============================================================
# CLI 入口
# ============================================================
if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print("DashScope 百炼全量模型路由器 — 双引擎协同中枢\n")
        print("用法: python tools/dashscope_router.py <task_type> <prompt> [options]\n")
        print("任务类型:")
        for m in list_available_models():
            print(f"  {m['task_type']:<22} → {m['model']:<32} | {m['description']}")
        print("\n选项:")
        print("  --image <path|url>  图片路径 / 视频路径或公网URL（多模态任务）")
        print("                      视频需 OSS 凭证: OSS_ACCESS_KEY_ID 等 4 个环境变量")
        print("  --files <paths>     文档路径列表（长文本任务）")
        print("  --size <WxH>        图像尺寸（图像生成，默认 1024x1024）")
        print("  --compare           展示跨平台模型对比（生成类任务）")
        print("  --role <角色名>      三方协同角色标注（如 主刀医生/质检护士）")
        print("  --prompt-file <path> 从文件读取长 Prompt（超长代码场景）")
        print("  --list              列出所有可用模型")
        print("\n示例:")
        print("  python tools/dashscope_router.py code '实现快速排序'")
        print("  python tools/dashscope_router.py long_text '总结' --files a.pdf b.docx")
        print("  python tools/dashscope_router.py image_analysis --image photo.jpg '描述图片'")
        print("  python tools/dashscope_router.py video_understanding --image video.mp4 '总结视频'")
        print("  python tools/dashscope_router.py video_understanding --image https://x.com/v.mp4 '总结'")
        print("  python tools/dashscope_router.py image_gen '赛博朋克城市' --compare")
        sys.exit(0)

    task_type = sys.argv[1]

    # --list
    if task_type == "--list" or task_type == "list":
        print(json.dumps(list_available_models(), indent=2, ensure_ascii=False))
        sys.exit(0)

    # 解析参数
    args = sys.argv[2:]
    prompt_parts = []
    kwargs = {}
    i = 0
    while i < len(args):
        if args[i] == "--image" and i + 1 < len(args):
            kwargs["image_path"] = args[i + 1]
            i += 2
        elif args[i] == "--files":
            i += 1
            files = []
            while i < len(args) and not args[i].startswith("--"):
                files.append(args[i])
                i += 1
            kwargs["files"] = files
        elif args[i] == "--size" and i + 1 < len(args):
            kwargs["size"] = args[i + 1]
            i += 2
        elif args[i] == "--compare":
            kwargs["compare"] = True
            i += 1
        elif args[i] == "--seed" and i + 1 < len(args):
            kwargs["seed"] = int(args[i + 1])
            i += 2
        elif args[i] == "--duration" and i + 1 < len(args):
            kwargs["duration"] = int(args[i + 1])
            i += 2
        elif args[i] == "--prompt-file" and i + 1 < len(args):
            try:
                with open(args[i + 1], "r", encoding="utf-8") as pf:
                    prompt_parts.append(pf.read())
            except Exception as e:
                print(f"读取 prompt 文件失败: {e}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] == "--role" and i + 1 < len(args):
            kwargs["role"] = args[i + 1]
            i += 2
        elif args[i] == "--n" and i + 1 < len(args):
            kwargs["n"] = int(args[i + 1])
            i += 2
        else:
            prompt_parts.append(args[i])
            i += 1

    prompt = " ".join(prompt_parts)

    # ── 冲突模型对比 ──
    if kwargs.get("compare") or task_type in ("image_gen", "video_gen_t2v", "video_gen_i2v"):
        comparison = show_conflict_comparison(task_type)
        if comparison:
            print(comparison, file=sys.stderr)
            # 在 CLI 模式下，对比表展示后直接使用百炼模型
            # （交互式场景应由 Claude 先展示对比再等用户确认）

    if not prompt:
        print("❌ 请提供 prompt 参数", file=sys.stderr)
        sys.exit(1)

    result = synergy_execute(task_type, prompt, **kwargs)
    print(result)
