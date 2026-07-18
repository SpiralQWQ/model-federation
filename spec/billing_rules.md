# 计费规则 — Token 账单分类与报告格式

> 模型联邦 V7.0 各模型的计费分类与使用成本计算标准。

## 计费分类

| 分类 | 说明 | 适用模型 |
|------|------|---------|
| 按量付费 (Pay-per-use) | 按 token 计费，实时扣减 | QwenMax, Gemini 3.5 Flash, GLM-4.7Flash |
| 套餐额度 (Allowance) | Go 套餐内不计消耗 | DeepSeek 主控会话 |
| 免费额度 (Free) | 零成本使用，有速率限制 | GLM-4.7Flash 免费调用, DeepSeek V4 Flash |
| 信用额度 (Credits) | 预充值按量扣除 | 智谱开放平台、阿里云百炼 |

## 计价参考

- 输入/输出价格因模型和平台而异，以各平台官网最新定价为准
- 模型调用后自动记录 token 消耗到计费日志

## 计费报告格式

每次模型调用后（或会话结束时），输出计费小结：

```
--- 计费小结 ---
模型: <模型名> | 输入: <hh>+<tt> tokens | 输出: <hh>+<tt> tokens
分类: <Pay-per-use / Allowance / Free / Credits>
费用: <金额> | 账户余额: <余额>
----------------
```

- `<hh>` 为命中缓存 token 数，`<tt>` 为非缓存 token 数
- 分类优先级：Free > Allowance > Credits > Pay-per-use（按最优惠分类展示）
- 汇总时仅列出实际调用过的模型
