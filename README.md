# AuditPilot — 审计合规智能分析 Demo

当前阶段：**M0+ 文档解析增强**。已完成：

- ✅ txt/md/csv 文本解析
- ✅ jpg/png/bmp/tiff/webp 图片 OCR（PaddleOCR/Tesseract）
- ✅ PDF/docx/xlsx 文档解析
- ✅ 扫描版 PDF OCR fallback
- ✅ Mock LLM（无 API key 也能跑）
- ✅ CI + ruff + pytest（34 tests）

**暂不实现：** ChromaDB、embedding、制度向量化、RAG、案例库、数据库、登录权限。

## 部署

见 [`docs/deployment.md`](docs/deployment.md)

## 快速启动

## Learning Path for Beginners

如果你是第一次看这个项目，不要从所有代码开始看。

请按这个顺序阅读：

1. `docs/learning/00_project_map.md`
2. `docs/learning/01_frontend_module.md`
3. `docs/learning/02_backend_module.md`
4. `docs/learning/03_data_module.md`
5. `docs/learning/04_request_flow.md`
6. `docs/learning/05_learning_checklist.md`

M0 阶段只需要理解一条主线：

```text
frontend 点击按钮 -> backend 接收请求 -> backend 返回 JSON -> frontend 显示结果
```

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
