# 多模态视觉双规验证 — 管线阶段

> **所属管线**：Phase 2（执行）
> **触发方式**：JIT 路由 → "图片/视觉"场景（触发词: 看图/截图/图片附件）
> **用途**：双轨视觉验证（Qwen-VL-MAX 主分析 + GLM-4.6V-Flash 交叉验证）
> **质量门禁**：Qwen + GLM 各自独立审查，均 ≥9.5 方通过

---

## 双轨架构

| 引擎 | 模型 | 角色 |
|------|------|------|
| 百炼视觉旗舰 | `qwen-vl-max` / `qwen3-vl-plus` | 主视觉分析（高精度细节） |
| 智谱免费视觉 | `GLM-4.6V-Flash` | 交叉验证（OCR 复核、细节查漏） |

## 执行规则

DeepSeek 对两者的提取结果进行交叉比对融合 → 提升识别精度 + 节省付费 Token。

默认图片分析用 Qwen-VL-MAX，用户说"Gemini"则切到 Playwright Edge 开 Gemini 网页版。

## 调用方式

```bash
# 默认视觉双规
python <YOUR_WORKSPACE>/tools/vision_analyzer.py <图片路径> "<提示词>" parallel

# 仅 Qwen-VL-MAX
python <YOUR_WORKSPACE>/scripts/dashscope_router.py image_analysis --image <路径>

# 仅 GLM 视觉
python <YOUR_WORKSPACE>/scripts/glm_router.py vision --image <路径> "描述"
```

## 禁止

直接用内置 Read 工具读取图片（必须走视觉双规）。

---
## 质检门禁（Phase 3 — Qwen + GLM 各自独立审查，均≥9.5 方通过）

### 检查项细则

| 检查项 | 具体判定标准 | Qwen 评分 | GLM 评分 |
|--------|------------|:---------:|:--------:|
| 双轨均执行 | Qwen-VL-MAX 和 GLM-4.6V-Flash 都调用了。只调一个 → 扣 5 分 | /10 | /10 |
| 交叉验证融合 | DeepSeek 对两者结果做了交叉比对。直接照搬一方 → 扣 3 分 | /10 | /10 |
| 禁止内置 Read | 未使用 Read 工具直接读图。用了 → 扣 5 分 | /10 | /10 |

### 通过条件

```
Qwen 评分 ≥ 9.5 AND GLM 评分 ≥ 9.5 → [质检] 裁决: 通过
Qwen 评分 < 9.5 OR GLM 评分 < 9.5 → [质检] 裁决: 返工（标注扣分项）
```
