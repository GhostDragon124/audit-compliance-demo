# Audit Compliance Demo

审计合规智能分析 M0+ demo。当前阶段只跑通最小端到端链路：前端上传文件并输入审核问题，后端保存文件、做基础解析，并返回 mock 或 OpenAI-compatible LLM 分析结果。

本阶段不实现 ChromaDB、embedding、制度向量化、RAG、案例库、数据库、登录权限或报告导出。

## Project Structure

```text
audit-compliance-demo/
  frontend/
  backend/
  data/
  docs/
```

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
fastapi dev app/main.py
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Environment

Copy the example file if you want to configure a real OpenAI-compatible chat completions endpoint:

```bash
cd backend
cp .env.example .env
```

`.env` fields:

```env
LLM_BASE_URL=http://your-qwen-api-server/v1
LLM_API_KEY=
LLM_MODEL=qwen3
```

If `LLM_API_KEY` is empty, the backend returns a mock response so the demo remains runnable.

## M0+ Implemented

- `GET /health`
- `POST /api/analyze`
- Multipart upload with multiple `files` and `question`
- Upload persistence under `backend/uploads/`
- Basic `.txt`, `.md`, and `.csv` parsing
- Unsupported file types return file-level `unsupported`
- Audit engine prompt composition
- OpenAI-compatible `/chat/completions` client
- Mock response fallback when no API key is configured
- React single-page upload and result display

## TODO

- PDF/docx/xlsx parsing
- ChromaDB regulation vector index
- `embedding_client`
- `vector_retriever`
- Qwen3 production integration
- Frontend display for retrieved regulation chunks
