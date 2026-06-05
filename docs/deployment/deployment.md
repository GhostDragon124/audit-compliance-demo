# AuditPilot 部署手册

> 目标环境：Linux (arm64/amd64)  
> 核心要求：审计材料不出院，OCR/LLM 本地执行

## 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | venv 方式安装 |
| Node.js | 20+ | 前端构建用 |
| LibreOffice | 24+ | .doc 文件转换 |
| 磁盘 | ≥10GB 空闲 | 依赖 + 制度文件 + ChromaDB 索引 |
| 内存 | ≥4GB | 仅 API 服务；模型推理需额外 GPU/显存 |

## 1. 拉取代码

```bash
git clone https://github.com/GhostDragon124/audit-compliance-demo.git
cd audit-compliance-demo
```

## 2. 后端部署

### 2.1 创建虚拟环境并安装依赖

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2.2 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# LLM 配置
LLM_MODE=openai_compatible              # mock | openai_compatible
LLM_BASE_URL=http://127.0.0.1:8083/v1   # 你的 LLM endpoint
LLM_API_KEY=                            # 本地 vLLM 无需鉴权
LLM_MODEL=your-model-name

# OCR 配置
OCR_PROVIDER=paddleocr                  # paddleocr | disabled
OCR_DEVICE=cpu
OCR_LANG=ch
OCR_ENABLE=true

# Embedding 配置（RAG 需要）
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_MODEL=your-embedding-model
EMBEDDING_BASE_URL=http://127.0.0.1:8085/v1

# RAG 模式
RAG_MODE=disabled                       # disabled | required
RAG_TOP_K=5

# ChromaDB
CHROMA_PERSIST_DIR=../data/indexes/chroma/regulations
CHROMA_COLLECTION_NAME=regulations

# 上传限制
MAX_FILE_SIZE_MB=50
MAX_TOTAL_UPLOAD_MB=100
MAX_FILES_PER_REQUEST=10
PDF_MAX_PAGES=100
```

`LLM_MODE=mock` 时无需 LLM 服务即可跑通 API。

### 2.3 安装 OCR 引擎

```bash
pip install paddleocr paddlepaddle
```

首次运行 PaddleOCR 会自动下载模型（约 30MB），后续使用离线缓存。

### 2.4 启动

```bash
cd backend
source .venv/bin/activate
fastapi run app/main.py --port 8000
```

验证：
```bash
curl http://127.0.0.1:8000/health
# → {"status":"ok"}
```

## 3. 前端部署

```bash
cd frontend
npm install
npm run build
```

静态文件在 `frontend/dist/`，可用任意 HTTP 服务器托管：

```bash
python3 -m http.server 5173 -d frontend/dist
```

> 前端默认向 `localhost:8000` 发 API 请求，如需修改代理目标请编辑 `frontend/vite.config.ts`。

## 4. 模型服务部署

### LLM（聊天模型）

需要 OpenAI-compatible `/chat/completions` 接口。

**vLLM 示例：**
```bash
vllm serve your-model --port 8083
```

**Ollama 示例：**
```bash
ollama serve
ollama pull qwen2.5:7b
# 端口默认 11434
```

然后在 `.env` 中配置对应的 `LLM_BASE_URL` 和 `LLM_MODEL`。

### Embedding 模型（RAG 需要）

**vLLM 示例：**
```bash
vllm serve your-embedding-model --port 8085
```

配置 `.env`：
```env
EMBEDDING_BASE_URL=http://127.0.0.1:8085/v1
EMBEDDING_MODEL=your-embedding-model
RAG_MODE=required
```

## 5. 制度文件索引（RAG 模式）

将制度文件放入 `data/regulations/raw/`，运行索引脚本：

```bash
cd backend
source .venv/bin/activate
python -m app.services.regulation_indexer
```

索引生成到 `data/indexes/chroma/regulations/`。

## 6. 完整测试

```bash
cd backend
source .venv/bin/activate
python -m compileall app
pip install pytest pytest-asyncio httpx
pytest -v -m "not production_rag"
```

预期：`151 passed`

> `production_rag` 标记的测试需要真实 Embedding 服务和 ChromaDB 索引，默认跳过。

## 7. 支持的文件格式

| 格式 | 说明 |
|------|------|
| .txt | 纯文本 |
| .md | Markdown |
| .csv | CSV 表格 |
| .docx | Word 文档（python-docx / 纯 XML） |
| .doc | 旧版 Word（LibreOffice headless 转换） |
| .xlsx | Excel（openpyxl / 纯 XML） |
| .png, .jpg, .bmp, .tiff, .webp | 图片（PaddleOCR 识别） |
| .pdf | PDF（PyMuPDF 文本提取 + 扫描页 OCR fallback） |

## 8. 数据不出院说明

| 组件 | 数据流向 |
|------|----------|
| OCR | 本地 PaddleOCR（离线缓存） |
| LLM | 本地 endpoint（127.0.0.1） |
| Embedding | 本地 endpoint（127.0.0.1） |
| 上传文件 | `backend/uploads/`（本地磁盘，请求后自动清理） |
| 制度文件 | `data/regulations/raw/`（本地磁盘） |
| 向量索引 | `data/indexes/chroma/`（本地磁盘） |

**所有数据均未离开本机。**

## 9. 故障排查

### Q: `ModuleNotFoundError: No module named 'fitz'`
```bash
pip install PyMuPDF
```

### Q: OCR 返回 `disabled`
OCR provider 未安装。检查：
```bash
python -c "from paddleocr import PaddleOCR; PaddleOCR(lang='ch')"
```
或在 `.env` 设置 `OCR_PROVIDER=disabled`。

### Q: `.doc` 文件解析失败
需安装 LibreOffice：
```bash
sudo apt install libreoffice
```

### Q: `/api/analyze` 返回 mock
`LLM_MODE=mock` 时系统返回固定 mock 响应。设为 `openai_compatible` 并确保 LLM 服务可达。

### Q: RAG 配置后检索为空
检查 `RAG_MODE=required`，确保 Embedding 服务可达且制度文件已索引。

### Q: 前端请求后端被 CORS 拦截
确认 `backend/app/main.py` 中 CORS origins 包含前端地址。
