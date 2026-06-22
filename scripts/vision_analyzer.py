"""
Universal Image Analyzer - calls external vision APIs automatically.
Supports: Gemini (free tier), Qwen (Aliyun, cheap), OpenAI (pay-per-use)
"""
import json
import sys
import io
import os
import base64
import urllib.request
import urllib.error

from PIL import Image

# ── Security: input validation constants ──────────────────────────
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}
MAX_IMAGE_PIXELS = 100_000_000  # ~10000×10000, prevents decompression-bomb DoS


def encode_image(image_path, max_size=2048):
    """Open, optionally resize, and base64-encode an image.

    Raises ValueError for unsupported formats; FileNotFoundError for
    missing / traversal paths; PIL.UnidentifiedImageError for corrupt files.
    """
    # ── file-type whitelist ──
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format: {ext or '<none>'}. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # ── path sanity (resolve symlinks / .. traversal) ──
    real_path = os.path.realpath(image_path)
    if not os.path.isfile(real_path):
        raise FileNotFoundError(f"Not a regular file: {image_path}")

    # ── decompression-bomb protection ──
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

    img = Image.open(image_path)

    w, h = img.size
    if max(w, h) > max_size:
        ratio = max_size / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        print(f"  [已压缩: {w}x{h} → {img.width}x{img.height}]", file=sys.stderr)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def call_qwen(image_path, prompt):
    """Call Aliyun DashScope Qwen-VL API (cheap, China-friendly)."""
    api_key = os.environ.get("QWEN_API_KEY")
    if not api_key:
        return {"error": "QWEN_API_KEY not set. Get one at https://dashscope.aliyun.com/"}

    img_b64 = encode_image(image_path)

    payload = {
        "model": "qwen-vl-max",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            ]
        }],
        "max_tokens": 1024,
        "temperature": 0.3
    }

    req = urllib.request.Request(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "choices" in result and result["choices"]:
                return {"text": result["choices"][0]["message"]["content"]}
            else:
                return {"error": f"Unexpected response: {json.dumps(result, indent=2)[:500]}"}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return {"error": f"Qwen API Error {e.code}: {body[:500]}"}
    except Exception as e:
        return {"error": f"Qwen request failed: {str(e)}"}


def call_gemini(image_path, prompt):
    """Call Google Gemini API (free tier)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY not set. Get one free at https://aistudio.google.com/apikey"}

    img_b64 = encode_image(image_path)

    url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"

    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/png", "data": img_b64}},
                {"text": prompt}
            ]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024,
            "topP": 0.95,
            "thinkingConfig": {"thinkingBudget": 0}
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
        ]
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "candidates" in result and result["candidates"]:
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return {"text": text}
            elif "promptFeedback" in result:
                return {"error": f"Blocked: {result['promptFeedback']}"}
            else:
                return {"error": f"Unexpected response: {json.dumps(result, indent=2)[:500]}"}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return {"error": f"Gemini API Error {e.code}: {body[:500]}"}
    except Exception as e:
        return {"error": f"Gemini request failed: {str(e)}"}


def call_openai(image_path, prompt):
    """Call OpenAI GPT-4o-mini API (pay-per-use, very cheap)."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set. Get one at https://platform.openai.com/api-keys"}

    img_b64 = encode_image(image_path)

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}", "detail": "high"}}
            ]
        }],
        "max_tokens": 1024,
        "temperature": 0.3
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "choices" in result and result["choices"]:
                return {"text": result["choices"][0]["message"]["content"]}
            else:
                return {"error": f"Unexpected response: {json.dumps(result, indent=2)[:500]}"}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return {"error": f"OpenAI API Error {e.code}: {body[:500]}"}
    except Exception as e:
        return {"error": f"OpenAI request failed: {str(e)}"}


def call_glm_vision(image_path, prompt):
    """Call GLM-4.6V-Flash (free tier) for cross-validation."""
    api_key = os.environ.get("GLM_API_KEY")
    if not api_key:
        return {"error": "GLM_API_KEY not set"}

    img_b64 = encode_image(image_path)

    payload = {
        "model": "glm-4.6v-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            ]
        }],
        "max_tokens": 1024,
        "temperature": 0.3
    }

    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "choices" in result and result["choices"]:
                return {"text": result["choices"][0]["message"]["content"]}
            else:
                return {"error": f"Unexpected: {json.dumps(result, indent=2)[:300]}"}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return {"error": f"GLM Vision Error {e.code}: {body[:300]}"}
    except Exception as e:
        return {"error": f"GLM Vision request failed: {str(e)}"}


if __name__ == "__main__":
    import concurrent.futures

    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print("Usage: python vision_analyzer.py <image_path> [prompt] [backend]")
        print("  backend: auto | qwen | gemini | openai | glm | parallel")
        sys.exit(1)

    path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "请详细描述这张图片的内容，包括其中所有的文字、物体、人物和场景。"
    backend = sys.argv[3] if len(sys.argv) > 3 else "parallel"

    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)

    print(f"[图像分析] 文件: {path}", file=sys.stderr)
    print(f"[图像分析] 后端: {backend}", file=sys.stderr)

    # ── 并行双规模式（默认）：Qwen-VL + GLM-4.6V-Flash 同时调用 ──
    if backend == "parallel":
        print("[双规验证] 并行调用 Qwen-VL + GLM-4.6V-Flash...", file=sys.stderr)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_qwen = executor.submit(call_qwen, path, prompt)
            future_glm = executor.submit(call_glm_vision, path, prompt)
            qwen_result = future_qwen.result()
            glm_result = future_glm.result()

        output = {
            "qwen_vl_max": qwen_result.get("text") or qwen_result.get("error", "unknown"),
            "glm_4_6v_flash": glm_result.get("text") or glm_result.get("error", "unknown"),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        if "error" in qwen_result:
            print(f"[双规] Qwen-VL 故障: {qwen_result['error']}", file=sys.stderr)
        if "error" in glm_result:
            print(f"[双规] GLM-4.6V-Flash 故障: {glm_result['error']}", file=sys.stderr)
        sys.exit(0 if "text" in qwen_result else 1)

    # ── 传统单后端模式（向后兼容） ──
    result = None

    try:
        if backend in ("auto", "qwen"):
            result = call_qwen(path, prompt)
            if "text" in result:
                print(result["text"])
                sys.exit(0)
            print(f"[Qwen] {result.get('error', 'unknown error')}", file=sys.stderr)
            if backend == "qwen":
                print(result["error"])
                sys.exit(1)

        if backend in ("auto", "gemini"):
            result = call_gemini(path, prompt)
            if "text" in result:
                print(result["text"])
                sys.exit(0)
            print(f"[Gemini] {result.get('error', 'unknown error')}", file=sys.stderr)
            if backend == "gemini":
                print(result["error"])
                sys.exit(1)

        if backend in ("auto", "glm"):
            result = call_glm_vision(path, prompt)
            if "text" in result:
                print(result["text"])
                sys.exit(0)
            print(f"[GLM Vision] {result.get('error', 'unknown error')}", file=sys.stderr)
            if backend == "glm":
                print(result["error"])
                sys.exit(1)

        if backend in ("auto", "openai"):
            result = call_openai(path, prompt)
            if "text" in result:
                print(result["text"])
                sys.exit(0)
            print(f"[OpenAI] {result.get('error', 'unknown error')}", file=sys.stderr)

        if result and "error" in result:
            print(result["error"])
        else:
            print("All backends failed.")
    except ValueError as e:
        print(f"Input validation failed: {e}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError as e:
        print(f"File error: {e}", file=sys.stderr)
        sys.exit(2)
