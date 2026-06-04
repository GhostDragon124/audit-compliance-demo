import csv
from pathlib import Path
from typing import Protocol

from app.config import get_settings
from app.schemas import ParsedFileSummary
from app.services.ocr_service import OCRService, SUPPORTED_IMAGE_SUFFIXES


class OCRTextExtractor(Protocol):
    def extract_text(self, image_path: Path) -> str:
        pass


class DocumentParser:
    text_suffixes = {".txt", ".md", ".csv"}
    image_suffixes = SUPPORTED_IMAGE_SUFFIXES
    supported_suffixes = text_suffixes | image_suffixes

    def __init__(self, ocr_service: OCRTextExtractor | None = None):
        self._ocr_service = ocr_service

    def parse(self, file_path: Path, original_filename: str) -> ParsedFileSummary:
        suffix = file_path.suffix.lower()
        if suffix not in self.supported_suffixes:
            return ParsedFileSummary(
                filename=original_filename,
                status="unsupported",
                preview="",
                error=f"Unsupported file type: {suffix or 'unknown'}",
            )

        if suffix in self.image_suffixes:
            return self._parse_image(file_path, original_filename)

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

    def _parse_image(self, file_path: Path, original_filename: str) -> ParsedFileSummary:
        try:
            content = self._get_ocr_service().extract_text(file_path)
            if not content.strip():
                return ParsedFileSummary(
                    filename=original_filename,
                    status="failed",
                    preview="",
                    error="No text detected in image",
                )

            return ParsedFileSummary(
                filename=original_filename,
                status="ocr_parsed",
                preview=self._preview(content),
            )
        except Exception as exc:
            return ParsedFileSummary(
                filename=original_filename,
                status="failed",
                preview="",
                error=str(exc),
            )

    def _get_ocr_service(self) -> OCRTextExtractor:
        if self._ocr_service is None:
            settings = get_settings()
            self._ocr_service = OCRService(
                provider=settings.ocr_provider,
                device=settings.ocr_device,
                lang=settings.ocr_lang,
                enabled=settings.ocr_enable,
            )
        return self._ocr_service

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
