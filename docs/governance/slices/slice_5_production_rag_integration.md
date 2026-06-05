# Slice 5: Production RAG Integration with Real Embedding

## Status

APPROVED

## Goal

将 Slice 4A–4C 已验证的 RAG 能力正式接入 `/api/analyze` 生产路径，使用真实 Qwen3-Embedding-4B 构造检索向量，从正式 ChromaDB Collection 检索制度，前端展示制度依据。

## Background

- 检索 + Prompt 接地 + E2E 在 Case 001 上已通过验收
- Embedding 服务 (8085) 运行正常，dim=2560
- Qwen 35B (8083) 运行正常
- 生产 Collection `regulations` 尚未建立
- `/api/analyze` 当前无 RAG 逻辑

## Non-goals

- 不实现制度版本治理、BM25、Hybrid、Reranker
- 不实现案例库、权限系统、多轮对话
- 不进行大规模 Prompt 调优
- 不重构前端

## Allowed files

```
backend/app/config.py
backend/app/main.py
backend/app/services/audit_engine.py
backend/app/services/embedding_client.py
backend/app/services/chroma_vector_store.py
backend/app/services/vector_retriever.py
backend/.env.example
backend/tests/**
docs/governance/**
```

## Forbidden files

```
data/tests/evaluation/case_001_procurement_pending_approval/**
data/regulations/**
frontend/** (前端已支持，无需修改)
```

## Required tests

### 单元/集成 (默认 CI，可 mock)
- test_rag_disabled_skips_retrieval
- test_rag_required_uses_real_embedding_provider_configuration
- test_required_rag_does_not_fallback_to_random_provider
- test_embedding_dimension_must_be_2560
- test_collection_metadata_mismatch_is_rejected
- test_embedding_connection_failure_returns_controlled_error
- test_no_related_regulations_is_not_treated_as_provider_failure
- test_production_collection_is_not_case001_collection
- test_api_analyze_returns_retrieved_regulations

### 真实 Provider (独立 marker: production_rag)
- Case 001 正式 API 验收 (POST /api/analyze)
- 浏览器手动验收

## Real provider acceptance

- Qwen3-Embedding-4B @ 8085 — dim=2560 必须验证
- Qwen 35B @ 8083
- 正式 ChromaDB Collection (regulations)
- 独立 marker: production_rag

## Definition of Done

- [ ] `/api/analyze` 正式路径自动执行 RAG (RAG_MODE=required)
- [ ] 正式 RAG 使用真实 Qwen3-Embedding-4B
- [ ] 正式路径不存在 RandomProvider fallback
- [ ] 普通 CI 仍可使用 fake embedding
- [ ] RAG_MODE 行为明确
- [ ] 正式 Collection 与 Case 001 Collection 隔离
- [ ] 正式 Collection Metadata 强校验
- [ ] Embedding 返回维度真实验证为 2560
- [ ] 检索失败与无结果严格区分
- [ ] 前端展示制度依据
- [ ] Case 001 通过正式 API 验收
- [ ] 默认测试全部通过
- [ ] 真实 Provider 测试通过
- [ ] Hermes 独立验证完成

## Rollback plan

- 将 `RAG_MODE` 设为 `disabled` 恢复非 RAG 行为
- 删除正式 Collection 并重建
- Git revert 到 slice-4c-complete
