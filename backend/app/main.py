import io
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

from app.config import get_settings
from app.schemas import AnalyzeResponse, ParsedFileSummary
from app.services.audit_engine import AuditEngine
from app.services.document_parser import DocumentParser
from app.services.llm_client import LLMClient, LLMConnectionError, LLMServiceError, LLMTimeoutError
from app.services.ocr_service import SUPPORTED_IMAGE_SUFFIXES

BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "uploads"
PROMPT_PATH = BASE_DIR / "app" / "prompts" / "audit_prompt.txt"

app = FastAPI(title="Audit Compliance Demo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    files: list[UploadFile] = File(default=[]),
    question: str = Form(...),
) -> AnalyzeResponse:
    settings = get_settings()
    if len(files) > settings.max_files_per_request:
        raise HTTPException(
            status_code=400,
            detail=f"单次最多上传 {settings.max_files_per_request} 个文件",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    parser = DocumentParser()
    if hasattr(parser, "configure"):
        parser.configure(settings)
    parsed_docs = []
    saved_paths: list[Path] = []
    validated_uploads: list[tuple[str, bytes]] = []
    total_size = 0

    for upload in files:
        safe_name = Path(upload.filename or "uploaded_file").name
        content = await upload.read()
        content_size = len(content)
        total_size += content_size

        if content_size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"单个文件最大 {settings.max_file_size_mb} MB",
            )

        suffix = Path(safe_name).suffix.lower()
        if suffix in SUPPORTED_IMAGE_SUFFIXES:
            _validate_image_dimensions(content, settings.image_max_pixels)

        validated_uploads.append((safe_name, content))

    if total_size > settings.max_total_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"单次上传总大小最大 {settings.max_total_upload_mb} MB",
        )

    for safe_name, content in validated_uploads:
        saved_name = f"{uuid4().hex}_{safe_name}"
        saved_path = UPLOAD_DIR / saved_name

        saved_path.write_bytes(content)
        saved_paths.append(saved_path)
        parsed_docs.append(parser.parse(saved_path, safe_name))

    llm_client = LLMClient(settings)
    audit_engine = AuditEngine(llm_client=llm_client, prompt_path=PROMPT_PATH, settings=settings)
    try:
        result = await audit_engine.analyze(question=question, parsed_files=parsed_docs)
    except LLMTimeoutError as exc:
        raise HTTPException(status_code=504, detail="模型服务超时，请稍后重试") from exc
    except LLMConnectionError as exc:
        raise HTTPException(status_code=503, detail="无法连接模型服务") from exc
    except LLMServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    finally:
        if settings.upload_cleanup:
            for saved_path in saved_paths:
                saved_path.unlink(missing_ok=True)
    result.parsed_files = [
        ParsedFileSummary(
            filename=doc.filename,
            status=doc.status,
            preview=doc.preview,
            error=doc.error,
        )
        for doc in parsed_docs
    ]
    return result


def _validate_image_dimensions(content: bytes, max_pixels: int) -> None:
    try:
        with Image.open(io.BytesIO(content)) as image:
            width, height = image.size
    except UnidentifiedImageError:
        return
    except Image.DecompressionBombError as exc:
        raise HTTPException(status_code=413, detail="图片尺寸过大") from exc

    if width * height > max_pixels:
        raise HTTPException(status_code=413, detail="图片尺寸过大")
