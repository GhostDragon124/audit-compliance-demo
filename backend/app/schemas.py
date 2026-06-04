from pydantic import BaseModel, Field


class ParsedFileSummary(BaseModel):
    filename: str
    status: str
    preview: str
    error: str | None = None


class RegulationChunk(BaseModel):
    chunk_id: str
    source_file: str
    content: str
    score: float | None = None
    metadata: dict = Field(default_factory=dict)


class AnalyzeResponse(BaseModel):
    answer_text: str
    parsed_files: list[ParsedFileSummary]
    retrieved_regulations: list[RegulationChunk]
