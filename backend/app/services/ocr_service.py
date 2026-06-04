from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


SUPPORTED_IMAGE_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
}


class OCRException(Exception):
    """Raised when OCR cannot be performed."""


class OCRProvider(ABC):
    @abstractmethod
    def extract(self, image_path: Path) -> str:
        """Extract text from an image path."""


class PaddleOCRProvider(OCRProvider):
    def __init__(self, lang: str = "ch", device: str = "cpu"):
        self.lang = lang
        self.device = device
        self.ocr = self._create_ocr()

    def extract(self, image_path: Path) -> str:
        try:
            result = self.ocr.ocr(str(image_path), cls=True)
        except TypeError:
            try:
                result = self.ocr.ocr(str(image_path))
            except Exception as exc:
                raise OCRException(f"PaddleOCR extraction failed: {exc}") from exc
        except Exception as exc:
            raise OCRException(f"PaddleOCR extraction failed: {exc}") from exc

        return "\n".join(_extract_paddle_text(result)).strip()

    def _create_ocr(self) -> Any:
        try:
            from paddleocr import PaddleOCR
        except Exception as exc:
            raise OCRException(f"PaddleOCR is unavailable: {exc}") from exc

        use_gpu = self.device.lower() not in {"cpu", ""}
        init_attempts = [
            {"lang": self.lang, "use_angle_cls": True, "use_gpu": use_gpu, "show_log": False},
            {"lang": self.lang, "use_angle_cls": True, "use_gpu": use_gpu},
            {"lang": self.lang},
        ]
        last_error: Exception | None = None
        for kwargs in init_attempts:
            try:
                return PaddleOCR(**kwargs)
            except TypeError as exc:
                last_error = exc
            except Exception as exc:
                raise OCRException(f"PaddleOCR initialization failed: {exc}") from exc

        raise OCRException(f"PaddleOCR initialization failed: {last_error}")


class TesseractProvider(OCRProvider):
    def __init__(self, lang: str = "ch"):
        self.lang = _tesseract_lang(lang)
        try:
            import pytesseract
            from PIL import Image
        except Exception as exc:
            raise OCRException(f"Tesseract OCR is unavailable: {exc}") from exc

        self._image = Image
        self._pytesseract = pytesseract

    def extract(self, image_path: Path) -> str:
        try:
            with self._image.open(image_path) as image:
                return self._pytesseract.image_to_string(image, lang=self.lang).strip()
        except Exception as exc:
            raise OCRException(f"Tesseract extraction failed: {exc}") from exc


class DisabledProvider(OCRProvider):
    def __init__(self, reason: str = "OCR is disabled"):
        self.reason = reason

    def extract(self, image_path: Path) -> str:
        raise OCRException(self.reason)


class OCRService:
    def __init__(
        self,
        provider: str | OCRProvider = "paddleocr",
        device: str = "cpu",
        lang: str = "ch",
        enabled: bool = True,
    ):
        self.provider = self._select_provider(provider, device=device, lang=lang, enabled=enabled)

    def extract_text(self, image_path: Path) -> str:
        """Extract text from image. May raise OCRException or return an empty string."""
        return self.provider.extract(image_path)

    def _select_provider(
        self,
        provider: str | OCRProvider,
        device: str,
        lang: str,
        enabled: bool,
    ) -> OCRProvider:
        if isinstance(provider, OCRProvider):
            return provider

        if not enabled:
            return DisabledProvider()

        provider_name = provider.lower().strip()
        if provider_name == "disabled":
            return DisabledProvider()
        if provider_name == "paddleocr":
            return _provider_with_fallback(lang=lang, device=device)
        if provider_name == "tesseract":
            try:
                return TesseractProvider(lang=lang)
            except OCRException as exc:
                return DisabledProvider(str(exc))

        return DisabledProvider(f"Unsupported OCR provider: {provider}")


def _provider_with_fallback(lang: str, device: str) -> OCRProvider:
    errors: list[str] = []
    try:
        return PaddleOCRProvider(lang=lang, device=device)
    except OCRException as exc:
        errors.append(str(exc))

    try:
        return TesseractProvider(lang=lang)
    except OCRException as exc:
        errors.append(str(exc))

    return DisabledProvider("; ".join(errors) or "OCR is disabled")


def _extract_paddle_text(result: Any) -> list[str]:
    texts: list[str] = []
    _collect_paddle_text(result, texts)
    return [text.strip() for text in texts if text.strip()]


def _collect_paddle_text(node: Any, texts: list[str]) -> None:
    if node is None:
        return

    if isinstance(node, dict):
        for key in ("text", "rec_text"):
            value = node.get(key)
            if isinstance(value, str):
                texts.append(value)
        rec_texts = node.get("rec_texts")
        if isinstance(rec_texts, list):
            texts.extend(str(item) for item in rec_texts if item)
        return

    if isinstance(node, tuple) and len(node) >= 2 and isinstance(node[0], str):
        texts.append(node[0])
        return

    if isinstance(node, (list, tuple)) and len(node) >= 2 and isinstance(node[1], (list, tuple)):
        text = node[1][0] if node[1] else None
        if isinstance(text, str):
            texts.append(text)
            return

    if isinstance(node, list):
        for item in node:
            _collect_paddle_text(item, texts)


def _tesseract_lang(lang: str) -> str:
    if lang.lower() in {"ch", "zh", "zh-cn", "chinese"}:
        return "chi_sim"
    return lang
