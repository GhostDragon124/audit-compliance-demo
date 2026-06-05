# Slice 2.7: LLM Robustness & Local Qwen Acceptance

> 基线：77 passed / 0 failed / 11 xfailed
> 模型：35B@8083 (qwen3.6-35b-a3b-fp8, no auth required)

## 目标

1. 显式 `LLM_MODE` 替代「有 API key → 真实 / 无 → mock」的隐式判断
2. 真实 Qwen 错误不伪装成正常审核结果
3. 本地 Qwen 无需鉴权

## 改动清单

### 1. config 新增

```python
llm_mode: str = "mock"  # "mock" | "openai_compatible"
llm_timeout: float = 120.0
```

### 2. llm_client 重构

```python
class LLMClient:
    async def chat_completion(self, prompt: str) -> str:
        if self.settings.llm_mode == "mock":
            return self._mock_response(prompt)
        if self.settings.llm_mode == "openai_compatible":
            return await self._openai_compatible(prompt)
        raise LLMError(f"Unknown LLM_MODE: {self.settings.llm_mode}")
    
    async def _openai_compatible(self, prompt: str) -> str:
        # Always call real API — even if api_key is empty
        headers = {"Content-Type": "application/json"}
        if self.settings.llm_api_key:  # Only add auth if key exists
            headers["Authorization"] = f"Bearer {self.settings.llm_api_key}"
        
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=...)
        except httpx.TimeoutException:
            raise LLMTimeoutError("网关超时")
        except httpx.ConnectError:
            raise LLMConnectionError("无法连接模型服务")
        
        if response.status_code >= 500:
            raise LLMServiceError(502, "模型服务异常")
        if response.status_code == 429:
            raise LLMServiceError(503, "模型服务繁忙")
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise LLMServiceError(502, "模型返回格式异常")
        
        if "choices" not in data:
            raise LLMServiceError(502, "模型返回缺少内容")
```

### 3. 错误类型

```python
class LLMError(Exception): ...
class LLMTimeoutError(LLMError): ...   # → 504
class LLMConnectionError(LLMError): ... # → 503
class LLMServiceError(LLMError): ...    # → 502
```

### 4. main.py 错误转 HTTP

```python
try:
    result = await engine.analyze(...)
except LLMTimeoutError:
    raise HTTPException(504, "模型服务超时，请稍后重试")
except LLMConnectionError:
    raise HTTPException(503, "无法连接模型服务")
except LLMServiceError as e:
    raise HTTPException(502, str(e))
```

### 5. 测试

- `test_llm_client_errors.py` (已存在)：更新以匹配新的 error 类型
- `test_local_provider_acceptance.py` (已存在)：更新以使用 `LLM_MODE=openai_compatible`
- 不新增 xfail

## 验收

```bash
cd backend && python -m pytest -q
# 0 failed, xfail 数量不增加
```
