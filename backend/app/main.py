from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import AnalyzeResponse
from app.services.audit_engine import AuditEngine
from app.services.document_parser import DocumentParser
from app.services.llm_client import LLMClient

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
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    parser = DocumentParser()
    parsed_files = []

    for upload in files:
        safe_name = Path(upload.filename or "uploaded_file").name
        saved_name = f"{uuid4().hex}_{safe_name}"
        saved_path = UPLOAD_DIR / saved_name

        content = await upload.read()
        saved_path.write_bytes(content)
        parsed_files.append(parser.parse(saved_path, safe_name))

    settings = get_settings()
    llm_client = LLMClient(settings)
    audit_engine = AuditEngine(llm_client=llm_client, prompt_path=PROMPT_PATH)
    return await audit_engine.analyze(question=question, parsed_files=parsed_files)
