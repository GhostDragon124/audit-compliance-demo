# Slice 3: Vector Index Infrastructure (并行轨道 A)

> 基线：94 passed / 0 failed / 2 xfailed
> Embedding 服务：Qwen3-Embedding-4B @ 8085, dim=2560
> 约束：禁止最终 audit_engine 集成，禁止用 preview 代替全文

## 目标

补齐 ChromaDB collection metadata，完成真实 embedding 验证，不碰 audit_engine。

## 改动清单

### 1. Collection Metadata（强制）

在 `chroma_vector_store.py` 创建/获取 collection 时写入 metadata：

```python
COLLECTION_METADATA = {
    "embedding_model": "Qwen3-Embedding-4B",
    "embedding_dimension": 2560,
    "distance_metric": "cosine",
    "chunk_strategy_version": "1.0",
    "index_schema_version": "1.0",
}
```

获取 collection 时校验 metadata，任一参数不匹配 → 抛错要求重建索引。

### 2. config 默认值修正

```python
embedding_provider: str = "openai_compatible"   # 从 random 改成真实
embedding_model: str = "/models"               # Qwen3-Embedding-4B 的 vLLM model ID
embedding_base_url: str = "http://127.0.0.1:8085/v1"
```

### 3. embedding_client 维度

`EmbeddingClient.__init__` 默认 `dim=2560`（匹配 Qwen3-Embedding-4B）。保留下游传参覆盖能力。

### 4. 测试

- `test_regulation_indexer.py`：已有测试保持通过，新增真实 embedding 验证测试
- `test_embedding_client.py`：已有通过
- `test_local_provider_acceptance.py`：新增 embedding 端点验收（BLOCKED if 8085 不通）
- **禁止**新增 audit_engine 测试
- **禁止**修改 test_analyze_api.py

### 5. 红线

- ❌ 不允许修改 audit_engine.py
- ❌ 不允许修改 main.py 中 analyze 路由的业务逻辑
- ❌ 不允许把 preview 当 full_text 送入 embedding
- ❌ 不允许宣称 RAG 链路完成

## 验收

```bash
cd backend && python -m pytest -q
# 94+ passed, 0 failed, xfailed 不增加
```
