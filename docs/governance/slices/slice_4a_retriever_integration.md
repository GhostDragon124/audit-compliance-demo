# Slice 4a: Retriever Integration

## Goal

将 VectorRetriever 接入 AuditEngine 编排流程，返回 `retrieved_regulations`，但暂不完成最终 RAG Prompt 和最终模型引用约束。

## Background

AuditPilot 已预留 regulation indexing、embedding 和 vector retrieval 模块。该 Slice 只定义未来将检索结果接入业务编排的边界，不在本治理迁移 Slice 中实现代码。

## Non-goals

- 不完成最终 RAG Prompt
- 不进行制度有效性治理
- 不加入案例库
- 不重构前端
- 不改变 Full Text Flow

## Case 001 test file paths

- `backend/tests/evaluation/test_case_001_retrieval.py`
- `backend/tests/evaluation/case_001_loader.py`

## xfail names

All tests in `TestRetrieval4A` class are strict xfail with reason containing `SLICE-4A`:

1. `test_build_isolated_index_and_retrieve_top5`
2. `test_relevant_regulations_in_top5`
3. `test_irrelevant_distractor_not_primary`
4. `test_retrieval_results_have_required_fields`

## DoD for xfail removal

When VectorRetriever is integrated with an isolated ChromaDB test index:

1. Build temp ChromaDB collection indexing Case 001 regulations
2. Embed with fake embedding (no real network call)
3. Query returns Top-5 results
4. Both 采购管理办法.txt and 采购审批管理规定.txt are in Top-5
5. 差旅费管理规定.txt is NOT in the top 2 positions
6. Each result item contains source_file, chunk_id, content, score/distance
7. All four 4A tests transition from xfail to normal pass

## Allowed files

Requires Project Owner approval before execution.

## Forbidden files

Requires Project Owner approval before execution.

## Required tests

- `backend/tests/evaluation/test_case_001_retrieval.py`

## Acceptance commands

```bash
cd backend
.venv/bin/python -m pytest tests/evaluation/test_case_001_retrieval.py -vv
```

## Risks

- 检索失败与无检索结果如果混淆，会误导审计辅助判断。
- 如果把 `preview` 当全文接入检索，会破坏 Full Text Flow 边界。
- 如果真实 Provider 测试进入普通 CI，会使基线依赖本地环境。

## Must Follow

- `audit_engine` 仍是唯一编排者
- `vector_retriever` 不调用 LLM
- 不得把 `preview` 当全文
- 检索失败与无检索结果必须区分
- 普通 CI 使用 fake embedding
- 真实 Provider 使用独立 marker

## Definition of Done

Requires Project Owner approval before execution.

## Status

PROPOSED — requires Project Owner approval before execution
