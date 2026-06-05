# AuditPilot — 审计合规智能分析 Demo

当前阶段：**Slice 5 Production RAG 集成完成**。151 tests / 0 xfailed，production_rag 3 passed。

## 已实现

### 文档解析
- ✅ txt / md / csv 文本解析
- ✅ PDF（PyMuPDF 文本提取 + 扫描页 OCR fallback）
- ✅ DOCX（python-docx + 表格提取）
- ✅ DOC（LibreOffice headless 转换）
- ✅ XLSX（openpyxl + 多 sheet）
- ✅ 混合 PDF 逐页 OCR（文本页/扫描页混合文档）
- ✅ 前端支持：txt / word / csv / png 文件选择
- ✅ OCR 页数超限 partial 报告

### OCR
- ✅ PaddleOCR（中文优化，离线可用，singleton 复用）
- ✅ 图片 OCR：jpg / png / bmp / tiff / webp
- ✅ Disabled provider（受控降级）

### LLM 集成
- ✅ 本地 Qwen3.6-35B-A3B-FP8 @ 8083（OpenAI 兼容，无需鉴权）
- ✅ 显式 `LLM_MODE=mock|openai_compatible`
- ✅ 真实 LLM 错误全路径受控（502/503/504，不伪装成正常结果）
- ✅ Token budget 控制 + 多文件按比例分配
- ✅ 截断明确提示（`[仅处理前 N 页，共 M 页]`）

### Embedding & 向量检索
- ✅ Qwen3-Embedding-4B @ 8085（dim=2560，vLLM arm64）
- ✅ ChromaDB 向量存储 + Collection metadata 校验
- ✅ RegulationIndexer（制度文件索引）
- ✅ VectorRetriever（语义检索）

### 上传安全
- ✅ 单文件大小限制（默认 50 MB）
- ✅ 总上传大小限制（默认 100 MB）
- ✅ 文件数量限制（默认 10 个）
- ✅ 图片尺寸限制
- ✅ PDF 页数限制
- ✅ 请求结束后上传文件自动清理

### Full Text Flow
- ✅ 内部 `ParsedDocument.full_text`（模型使用完整文本）
- ✅ API 层只暴露 `preview`（安全边界）
- ✅ Token budget 比例分配

### 工程质量
- ✅ pytest 151 tests / 0 xfailed + 3 production_rag tests
- ✅ CI（pytest + ruff + CodeQL）
- ✅ 前端 build 通过

## 部署

| 服务 | 端口 | 模型 | 说明 |
|------|------|------|------|
| 35B Chat | 8083 | `qwen3.6-35b-a3b-fp8` | vLLM arm64 |
| Embedding | 8085 | `Qwen3-Embedding-4B` | vLLM arm64, dim=2560 |
| AuditPilot API | 8000 | FastAPI | `cd backend && fastapi dev` |

部署文档详见：
- [`docs/deployment/deployment.md`](docs/deployment/deployment.md) — 项目部署指南

## 快速启动

```bash
# Backend
cd backend
cp .env.example .env        # 首次运行
uv pip install -r requirements.txt
fastapi dev app/main.py

# Frontend
cd frontend
npm install
npm run dev
```

## 环境变量

```env
# LLM
LLM_MODE=mock                          # mock | openai_compatible
LLM_BASE_URL=http://127.0.0.1:8083/v1
LLM_API_KEY=                           # 本地 vLLM 无需鉴权
LLM_MODEL=qwen3.6-35b-a3b-fp8

# OCR
OCR_PROVIDER=paddleocr

# Embedding
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_MODEL=/models
EMBEDDING_BASE_URL=http://127.0.0.1:8085/v1

# Vector
CHROMA_PERSIST_DIR=../data/indexes/chroma/regulations
CHROMA_COLLECTION_NAME=regulations

# Upload
MAX_FILE_SIZE_MB=50
MAX_TOTAL_UPLOAD_MB=100
MAX_FILES_PER_REQUEST=10
PDF_MAX_PAGES=100
```

`LLM_MODE=mock` 时返回固定 mock 响应，无需模型服务也能跑。

## API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/analyze` | 上传文件 + 问题 → 审计分析 |

## Project Structure

```text
audit-compliance-demo/
├── frontend/          # React + Vite + TypeScript
├── backend/
│   ├── app/
│   │   ├── config.py           # pydantic-settings
│   │   ├── main.py             # FastAPI routes
│   │   ├── models.py           # ParsedDocument
│   │   ├── schemas.py          # API schemas
│   │   ├── prompts/            # Prompt templates
│   │   └── services/
│   │       ├── audit_engine.py
│   │       ├── chroma_vector_store.py
│   │       ├── document_parser.py
│   │       ├── embedding_client.py
│   │       ├── llm_client.py
│   │       ├── ocr_service.py
│   │       ├── regulation_indexer.py
│   │       └── vector_retriever.py
│   ├── tests/          # 99 tests / 0 xfailed
│   └── requirements.txt
├── data/
│   ├── regulations/    # 制度文件
│   └── indexes/        # ChromaDB
└── docs/
    ├── deployment/
    ├── devlog/
    └── learning/
```
