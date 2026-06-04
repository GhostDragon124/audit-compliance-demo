from collections.abc import AsyncGenerator
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import app  # noqa: E402


FIXTURES_DIR = Path(__file__).parent / "fixtures"
PROMPT_PATH = Path(__file__).parents[1] / "app" / "prompts" / "audit_prompt.txt"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def prompt_path() -> Path:
    return PROMPT_PATH


@pytest.fixture
def mock_settings() -> Settings:
    return Settings(llm_api_key="")


@pytest_asyncio.fixture
async def client(
    monkeypatch: pytest.MonkeyPatch,
    mock_settings: Settings,
    tmp_path: Path,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    monkeypatch.setattr("app.main.get_settings", lambda: mock_settings)
    monkeypatch.setattr("app.main.UPLOAD_DIR", tmp_path / "uploads")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client
