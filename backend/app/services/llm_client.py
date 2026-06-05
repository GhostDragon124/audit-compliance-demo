from typing import Any

import httpx

from app.config import Settings


class LLMError(Exception):
    pass


class LLMTimeoutError(LLMError):
    pass


class LLMConnectionError(LLMError):
    pass


class LLMServiceError(LLMError):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(message)


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def chat_completion(self, prompt: str) -> str:
        if self.settings.llm_mode == "mock":
            return self._mock_response(prompt)
        if self.settings.llm_mode == "openai_compatible":
            return await self._openai_compatible(prompt)
        raise LLMError(f"Unknown LLM_MODE: {self.settings.llm_mode}")

    async def _openai_compatible(self, prompt: str) -> str:
        base_url = self.settings.llm_base_url.rstrip("/")
        url = f"{base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": "你是一个审计合规辅助分析助手。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        headers = {"Content-Type": "application/json"}
        if self.settings.llm_api_key:
            headers["Authorization"] = f"Bearer {self.settings.llm_api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("网关超时") from exc
        except httpx.ConnectError as exc:
            raise LLMConnectionError("无法连接模型服务") from exc
        except httpx.RequestError as exc:
            raise LLMConnectionError("模型服务请求失败") from exc

        status_code = getattr(response, "status_code", 200)
        if status_code == 429:
            raise LLMServiceError(503, "模型服务繁忙")
        if status_code >= 500:
            raise LLMServiceError(502, "模型服务异常")
        if status_code >= 400:
            raise LLMServiceError(502, f"模型服务返回错误: HTTP {status_code}")

        try:
            data = response.json()
        except ValueError as exc:
            raise LLMServiceError(502, "模型返回格式异常") from exc

        return self._extract_message_content(data)

    def _extract_message_content(self, data: Any) -> str:
        if not isinstance(data, dict) or "choices" not in data:
            raise LLMServiceError(502, "模型返回缺少内容")

        choices = data["choices"]
        if not isinstance(choices, list) or not choices:
            raise LLMServiceError(502, "模型返回缺少内容")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise LLMServiceError(502, "模型返回缺少内容")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise LLMServiceError(502, "模型返回缺少内容")

        content = message.get("content")
        if not isinstance(content, str):
            raise LLMServiceError(502, "模型返回缺少内容")

        return content

    def _mock_response(self, prompt: str) -> str:
        return (
            "一、总体判断\n"
            "- AI 初步判断：已收到上传材料和审核问题，当前返回 mock 初步审核意见。\n"
            "- 风险等级：待人工复核\n"
            "- 简要说明：系统当前 LLM_MODE=mock，因此未调用真实模型。本次仅基于 demo 流程返回固定示例。\n\n"
            "二、可能存在的问题\n"
            "- 问题：需要结合完整材料进一步核实是否存在流程、金额、审批或凭证方面的异常。\n"
            "- 涉及材料：以上传文件解析预览为准。\n"
            "- 风险说明：当前材料证据不足，无法形成最终审计结论。\n"
            "- 建议人工复核点：请重点核对审批链路、原始凭证、金额一致性和相关制度要求。\n\n"
            "三、缺失或不确定的信息\n"
            "当前未接入制度检索、案例库和完整文档解析能力，可能缺少制度条款、上下文材料和历史对比信息。\n\n"
            "四、免责声明\n"
            "本结果由 AI 根据当前上传材料生成，仅供审计人员辅助参考，不构成最终审计结论。"
        )
