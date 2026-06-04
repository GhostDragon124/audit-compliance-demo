# AuditPilot 部署手册

> 目标环境：院内 Ubuntu 24.04 机器  
> 核心要求：审计材料不出院，OCR/LLM 本地执行

## 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.13+ | venv 方式安装 |
| Node.js | 22+ | 前端构建用 |
| 磁盘 | ≥5GB 空闲 | 依赖 + 模型 + uploads |
| 内存 | ≥8GB | OCR 推理需要 |

## 1. 拉取代码

```bash
git clone https://github.com/GhostDragon124/audit-compliance-demo.git
cd audit-compliance-demo
git checkout master
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
# LLM 配置（连接本地 Qwen/DeepSeek 服务）
LLM_BASE_URL=http://127.0.0.1:8000/v1
LLM_API_KEY=local-dummy-key
LLM_MODEL=qwen-local

# OCR 配置
# paddleocr: 优先，适合中文扫描件，本地执行
# tesseract: 备选，需额外安装 tesseract 二进制
# disabled: 禁用 OCR
OCR_PROVIDER=paddleocr
OCR_DEVICE=cpu
OCR_LANG=ch
OCR_ENABLE=true
```

### 2.3 安装 OCR 引擎（二选一）

**方案 A: PaddleOCR（推荐）**
```bash
pip install paddleocr paddlepaddle
```

**方案 B: Tesseract（轻量备选）**
```bash
sudo apt install tesseract-ocr tesseract-ocr-chi-sim
```

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

静态文件在 `frontend/dist/`，可用 nginx 托管或直接用：

```bash
npx serve dist -l 5173
```

## 4. LLM 端点配置

本地 LLM 需暴露 OpenAI-compatible `/chat/completions` 接口。

**vLLM 示例：**
```bash
vllm serve Qwen/Qwen2.5-7B-Instruct --port 8000
```

**Ollama 示例：**
```bash
ollama serve
ollama pull qwen2.5:7b
```

然后在 `.env` 中配置：
```env
LLM_BASE_URL=http://127.0.0.1:11434/v1    # Ollama
LLM_MODEL=qwen2.5:7b
```

## 5. 完整测试

```bash
cd backend
source .venv/bin/activate
python -m compileall app
pip install pytest pytest-asyncio httpx
pytest -v
```

预期：`34 passed`

## 6. 数据不出院说明

| 组件 | 数据流向 |
|------|----------|
| OCR | 本地 PaddleOCR/Tesseract |
| LLM | 本地 endpoint（127.0.0.1） |
| 上传文件 | `backend/uploads/`（本地磁盘） |
| 法规文件 | `data/regulations/raw/`（本地磁盘） |
| 向量索引 | `data/indexes/chroma/`（本地磁盘） |

**所有数据均未离开本机。**

## 7. 故障排查

### Q: `ModuleNotFoundError: No module named 'fitz'`
```bash
pip install PyMuPDF
```

### Q: OCR 返回 `disabled`
OCR provider 未安装或初始化失败。检查：
```bash
python -c "from paddleocr import PaddleOCR; PaddleOCR(lang='ch')"
```
如果失败，改用 tesseract 或在 `.env` 设置 `OCR_ENABLE=false`。

### Q: `/api/analyze` 返回 mock 而非真实 LLM 结果
检查 `LLM_API_KEY` 是否为空。为空时系统自动返回 mock。

### Q: `LLM_API_KEY` 已配置但调用失败
检查 LLM endpoint 是否可达：
```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local-dummy-key" \
  -d '{"model":"qwen-local","messages":[{"role":"user","content":"hello"}]}'
```

### Q: 前端请求后端被 CORS 拦截
确认 `backend/app/main.py` 中 CORS origins 包含前端地址。默认允许 `localhost:5173`。

### Q: 测试报 `Name or service not known`
DNS/网络问题。确认机器能访问 PyPI，或使用离线安装方式。
