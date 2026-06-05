# Slice 2.6: Full Text Flow & Explicit Truncation

> 日期：2026-06-05  
> 基线：73 passed / 0 failed / 14 xfailed  
> 模型就绪：35B@8083 (id=/models, max_model_len=131072), Embedding@8085 (dim=2560)

## 目标

修复当前最大业务缺陷：LLM 只收到 1000 字符 preview，而非完整解析文本。

## 设计原则

1. **API 契约不动**：`/api/analyze` 响应不新增字段，已有字段语义不变
2. **内部增强**：后端内部携带 `full_text`，API 层只暴露 `preview`
3. **Token budget 控制**：不是无限全文，也不是固定 1000 字

---

## 改动清单

### 1. 新增内部模型 `ParsedDocument`

文件：`backend/app/models.py`（新文件）

```python
from dataclasses import dataclass, field

@dataclass
class ParsedDocument:
    filename: str
    status: str           # "parsed" | "failed" | "unsupported"
    full_text: str        # 完整文本，内部使用
    preview: str          # API 暴露（<= 1000 chars）
    error: str | None = None
    is_truncated: bool = False       # full_text 是否被截断
    original_chars: int = 0          # 原始总字符数
    used_chars: int = 0              # 实际送入模型的字符数
    truncation_notice: str = ""      # 截断提示文案
```

### 2. `DocumentParser` 返回 `ParsedDocument`

- `parse()` 方法返回 `ParsedDocument` 而非 `ParsedFileSummary`
- `full_text` 存完整解析文本
- `preview` = `_preview(full_text, max_length=PREVIEW_MAX_LENGTH)`
- 调用方（`main.py` 路由）内部持有 `ParsedDocument`，序列化到 API 时只取 `filename/status/preview/error`

### 3. `TokenBudget` 配置

新增 config：

```python
# config.py
llm_mode: str = "mock"                    # "mock" | "openai_compatible"
llm_max_prompt_chars: int = 24000         # ~6000 tokens (中英文混合)
llm_truncation_prompt_template: str = (
    "\n\n[分析范围提示]\n"
    "以下材料已被截断：原始 {original_chars} 字符，本次分析使用前 {used_chars} 字符。\n"
)
```

### 4. `AuditEngine` 改进

- `_build_prompt` 遍历 `ParsedDocument.full_text`（非 `preview`）
- 多文件按字符数比例分配 token budget
- 达到 budget 上限时截断 + 注入 `truncation_notice`
- `_build_truncation_notice()` 在 `answer_text` 前拼接统一的范围提示

### 5. `main.py` 路由适配

```python
# 旧：ParsedFileSummary → 直接序列化
# 新：ParsedDocument → 转换 → ParsedFileSummary（API 暴露）
parsed_docs: list[ParsedDocument] = ...
parsed_summaries = [
    ParsedFileSummary(
        filename=doc.filename,
        status=doc.status,
        preview=doc.preview,
        error=doc.error,
    )
    for doc in parsed_docs
]
```

### 6. 测试

- `test_audit_engine_receives_full_text_not_only_preview`：**xfail → pass**（Sentinel 必须在 prompt 中）
- `test_long_document_truncation_is_explicit`：**xfail → pass**（截断提示必须出现在 prompt 中）
- `test_failed_document_content_is_not_treated_as_valid`：**xfail → pass**（失败文件内容不进入 prompt）
- API 测试保持不变（API 响应格式不变）
- 新增：`test_token_budget_distribution`（多文件预算分配）
- 新增：`test_full_text_not_leaked_in_api`（full_text 不泄露到 API）
- 所有 73 个通过测试保持通过

---

## 依赖

- 无新增依赖
- 需创建 `backend/.env`（从 `.env.example` 复制）

## 验收标准

```bash
cd backend && python -m pytest -q
# 预期：14 xfailed → ≤ 11 xfailed（3 个转为 pass）
# 0 failed
```
