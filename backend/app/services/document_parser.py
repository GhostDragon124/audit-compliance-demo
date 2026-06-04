import csv
from pathlib import Path

from app.schemas import ParsedFileSummary


class DocumentParser:
    supported_suffixes = {".txt", ".md", ".csv"}

    def parse(self, file_path: Path, original_filename: str) -> ParsedFileSummary:
        suffix = file_path.suffix.lower()
        if suffix not in self.supported_suffixes:
            return ParsedFileSummary(
                filename=original_filename,
                status="unsupported",
                preview="",
                error=f"Unsupported file type: {suffix or 'unknown'}",
            )

        try:
            if suffix == ".csv":
                content = self._read_csv_preview(file_path)
            else:
                content = file_path.read_text(encoding="utf-8", errors="replace")

            return ParsedFileSummary(
                filename=original_filename,
                status="parsed",
                preview=self._preview(content),
            )
        except Exception as exc:
            return ParsedFileSummary(
                filename=original_filename,
                status="failed",
                preview="",
                error=str(exc),
            )

    def _read_csv_preview(self, file_path: Path) -> str:
        rows: list[str] = []
        with file_path.open("r", encoding="utf-8", errors="replace", newline="") as csv_file:
            reader = csv.reader(csv_file)
            for index, row in enumerate(reader):
                if index >= 20:
                    break
                rows.append(", ".join(row))
        return "\n".join(rows)

    def _preview(self, content: str, max_length: int = 1000) -> str:
        normalized = content.strip()
        if len(normalized) <= max_length:
            return normalized
        return f"{normalized[:max_length]}..."
