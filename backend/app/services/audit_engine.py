from pathlib import Path

from app.config import Settings, get_settings
from app.models import ParsedDocument
from app.schemas import AnalyzeResponse, ParsedFileSummary, RegulationChunk
from app.services.llm_client import LLMClient


ParsedAuditInput = ParsedDocument | ParsedFileSummary
VALID_CONTENT_STATUSES = {"parsed", "ocr_parsed"}


class AuditEngine:
    def __init__(self, llm_client: LLMClient, prompt_path: Path, settings: Settings | None = None):
        self.llm_client = llm_client
        self.prompt_template = prompt_path.read_text(encoding="utf-8")
        self.settings = settings or get_settings()

    async def analyze(
        self,
        question: str,
        parsed_files: list[ParsedAuditInput],
    ) -> AnalyzeResponse:
        prompt, truncation_notice = self._build_prompt_with_notice(question, parsed_files)
        answer_text = await self.llm_client.chat_completion(prompt)
        if truncation_notice:
            answer_text = f"{truncation_notice}{answer_text}"
        return AnalyzeResponse(
            answer_text=answer_text,
            parsed_files=[self._to_summary(parsed_file) for parsed_file in parsed_files],
            retrieved_regulations=[],
        )

    def _build_prompt(self, question: str, parsed_files: list[ParsedAuditInput]) -> str:
        prompt, _ = self._build_prompt_with_notice(question, parsed_files)
        return prompt

    def _build_prompt_with_notice(
        self,
        question: str,
        parsed_files: list[ParsedAuditInput],
    ) -> tuple[str, str]:
        file_sections, truncation_notice = self._build_file_sections(parsed_files)
        files_text = "\n\n".join(file_sections) if file_sections else "未上传文件"
        if truncation_notice and file_sections:
            files_text = f"{truncation_notice}{files_text}"

        prompt = (
            f"{self.prompt_template}\n\n"
            f"用户审核问题：\n{question}\n\n"
            "上传材料解析结果：\n"
            f"{files_text}"
        )
        return prompt, truncation_notice

    def build_rag_prompt(
        self,
        question: str,
        parsed_files: list[ParsedAuditInput],
        retrieved_regulations: list[RegulationChunk],
    ) -> str:
        """Build a prompt that includes material full text, regulation fragments
        with source references, and a manual confirmation disclaimer.

        This is a public method used by tests and by the analyze() flow.
        """
        file_sections, truncation_notice = self._build_file_sections(parsed_files)
        files_text = "\n\n".join(file_sections) if file_sections else "未上传文件"
        if truncation_notice and file_sections:
            files_text = f"{truncation_notice}{files_text}"

        # Build regulation fragments section
        regulation_lines: list[str] = []
        for reg in retrieved_regulations:
            regulation_lines.append(
                f"制度文件: {reg.source_file} (块: {reg.chunk_id})\n{reg.content}"
            )
        regulations_text = "\n---\n".join(regulation_lines) if regulation_lines else ""

        if regulations_text:
            prompt = (
                f"{self.prompt_template}\n\n"
                f"用户审核问题：\n{question}\n\n"
                "上传材料解析结果：\n"
                f"{files_text}\n\n"
                "## 相关制度依据\n"
                f"{regulations_text}\n\n"
                "注意：以上制度内容由系统检索并提供，其有效性和适用性需要人工确认。"
                "本结果由 AI 根据当前材料生成，仅供审计人员辅助参考。"
            )
        else:
            prompt = (
                f"{self.prompt_template}\n\n"
                f"用户审核问题：\n{question}\n\n"
                "上传材料解析结果：\n"
                f"{files_text}"
            )
        return prompt

    def _build_file_sections(self, parsed_files: list[ParsedAuditInput]) -> tuple[list[str], str]:
        full_texts = [self._valid_full_text(parsed_file) for parsed_file in parsed_files]
        budgets = self._allocate_char_budget([len(text) for text in full_texts])

        file_sections: list[str] = []
        original_total = 0
        used_total = 0
        for parsed_file, full_text, budget in zip(parsed_files, full_texts, budgets):
            original_chars = len(full_text)
            used_chars = min(original_chars, budget)
            original_total += original_chars
            used_total += used_chars
            is_truncated = used_chars < original_chars
            content = full_text[:used_chars]

            if isinstance(parsed_file, ParsedDocument):
                parsed_file.original_chars = original_chars
                parsed_file.used_chars = used_chars
                parsed_file.is_truncated = is_truncated
                parsed_file.truncation_notice = (
                    self._build_truncation_notice(original_chars, used_chars) if is_truncated else ""
                )

            lines = [
                f"文件名：{parsed_file.filename}",
                f"解析状态：{parsed_file.status}",
                f"错误信息：{parsed_file.error or '无'}",
            ]
            if parsed_file.status in VALID_CONTENT_STATUSES:
                lines.append(f"材料内容：\n{content or '无可用内容'}")
            else:
                lines.append("材料内容：\n无可用内容")
            file_sections.append("\n".join(lines))

        truncation_notice = ""
        if used_total < original_total:
            truncation_notice = self._build_truncation_notice(original_total, used_total)
        return file_sections, truncation_notice

    def _valid_full_text(self, parsed_file: ParsedAuditInput) -> str:
        if parsed_file.status not in VALID_CONTENT_STATUSES:
            return ""
        full_text = getattr(parsed_file, "full_text", None)
        if full_text is None:
            full_text = parsed_file.preview
        return full_text.strip()

    def _allocate_char_budget(self, lengths: list[int]) -> list[int]:
        if not lengths:
            return []

        total = sum(lengths)
        budget = max(0, self.settings.llm_max_prompt_chars)
        if total <= budget:
            return lengths.copy()
        if budget == 0 or total == 0:
            return [0 for _ in lengths]

        allocations = [0 for _ in lengths]
        fractional_parts: list[tuple[int, float]] = []
        for index, length in enumerate(lengths):
            if length <= 0:
                fractional_parts.append((index, 0.0))
                continue
            raw_allocation = budget * (length / total)
            whole_allocation = min(int(raw_allocation), length)
            allocations[index] = whole_allocation
            fractional_parts.append((index, raw_allocation - int(raw_allocation)))

        leftover = budget - sum(allocations)
        for index, _ in sorted(fractional_parts, key=lambda item: item[1], reverse=True):
            if leftover <= 0:
                break
            if allocations[index] < lengths[index]:
                allocations[index] += 1
                leftover -= 1

        if leftover <= 0:
            return allocations

        for index in sorted(range(len(lengths)), key=lambda item: lengths[item], reverse=True):
            if leftover <= 0:
                break
            available = lengths[index] - allocations[index]
            if available <= 0:
                continue
            addition = min(available, leftover)
            allocations[index] += addition
            leftover -= addition

        return allocations

    def _build_truncation_notice(self, original_chars: int, used_chars: int) -> str:
        return self.settings.llm_truncation_prompt_template.format(
            original_chars=original_chars,
            used_chars=used_chars,
        )

    def _to_summary(self, parsed_file: ParsedAuditInput) -> ParsedFileSummary:
        if isinstance(parsed_file, ParsedFileSummary):
            return parsed_file
        return ParsedFileSummary(
            filename=parsed_file.filename,
            status=parsed_file.status,
            preview=parsed_file.preview,
            error=parsed_file.error,
        )
