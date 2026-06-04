from pathlib import Path

from app.schemas import AnalyzeResponse, ParsedFileSummary
from app.services.llm_client import LLMClient


class AuditEngine:
    def __init__(self, llm_client: LLMClient, prompt_path: Path):
        self.llm_client = llm_client
        self.prompt_template = prompt_path.read_text(encoding="utf-8")

    async def analyze(
        self,
        question: str,
        parsed_files: list[ParsedFileSummary],
    ) -> AnalyzeResponse:
        prompt = self._build_prompt(question, parsed_files)
        answer_text = await self.llm_client.chat_completion(prompt)
        return AnalyzeResponse(
            answer_text=answer_text,
            parsed_files=parsed_files,
            retrieved_regulations=[],
        )

    def _build_prompt(self, question: str, parsed_files: list[ParsedFileSummary]) -> str:
        file_sections = []
        for parsed_file in parsed_files:
            file_sections.append(
                "\n".join(
                    [
                        f"文件名：{parsed_file.filename}",
                        f"解析状态：{parsed_file.status}",
                        f"错误信息：{parsed_file.error or '无'}",
                        f"内容预览：\n{parsed_file.preview or '无可用预览'}",
                    ]
                )
            )

        files_text = "\n\n".join(file_sections) if file_sections else "未上传文件"

        return (
            f"{self.prompt_template}\n\n"
            f"用户审核问题：\n{question}\n\n"
            "上传材料解析结果：\n"
            f"{files_text}"
        )
