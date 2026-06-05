# Slice 4b: RAG Prompt Grounding

## Goal

实现 AuditEngine 的 RAG Prompt 构建逻辑，确保：

1. 材料全文（非 preview）进入 Prompt
2. 检索到的相关制度片段正确嵌入 Prompt
3. 每个制度片段附带 source_file 和 chunk_id 引用
4. Prompt 不将 preview 当作全文
5. 无关干扰制度不成为主要依据
6. Prompt 保留"制度有效性需人工确认"免责声明

## Non-goals

- 不接入真实 Qwen
- 不接入真实 Embedding
- 不实现 VectorRetriever（由 Slice 4A 提供）
- 不改变 Full Text Flow
- 不修改文档解析逻辑
- 不实现案例库

## Required tests

- `backend/tests/evaluation/test_case_001_prompt_grounding.py`

Tests (all strict xfail with reason `SLICE-4B`):

| Test Name | Target |
|-----------|--------|
| `test_prompt_contains_material_full_text` | 材料全文进入 Prompt |
| `test_prompt_contains_regulation_fragments` | 制度片段进入 Prompt |
| `test_prompt_includes_source_references` | 附带 source_file + chunk_id |
| `test_prompt_does_not_use_preview_as_full_text` | 不把 preview 当全文 |
| `test_prompt_does_not_use_irrelevant_distractor_as_primary` | 干扰制度不作为主要依据 |
| `test_prompt_has_manual_confirmation_disclaimer` | 免责声明保留 |

## Forbidden integrations

- 真实 Qwen 调用（必须使用 fake LLM）
- 真实 Embedding 调用（必须使用 fake embedding）
- 真实 ChromaDB（必须使用 fake retriever）
- 任何网络调用

## Definition of Done

1. All 6 tests in `test_case_001_prompt_grounding.py` pass normally (xfail removed)
2. Tests use fake retriever + fake LLM only
3. No real network calls
4. No production code changes outside allowed files

## Status

PROPOSED — requires Project Owner approval before execution
