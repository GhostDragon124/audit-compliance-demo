from dataclasses import dataclass


@dataclass
class ParsedDocument:
    filename: str
    status: str
    full_text: str
    preview: str
    error: str | None = None
    is_truncated: bool = False
    original_chars: int = 0
    used_chars: int = 0
    truncation_notice: str = ""
