from typing import Any

import httpx

from app.config import Settings


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def chat_completion(self, prompt: str) -> str:
        if not self.settings.llm_api_key:
            return self._mock_response(prompt)

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
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"]

    def _mock_response(self, prompt: str) -> str:
        return (
            "一、总体判断\n"
            "- AI 初步判断：已收到上传材料和审核问题，当前返回 mock 初步审核意见。\n"
            "- 风险等级：待人工复核\n"
            "- 简要说明：系统尚未配置 LLM_API_KEY，因此未调用真实模型。本次仅基于 demo 流程返回固定示例。\n\n"
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
