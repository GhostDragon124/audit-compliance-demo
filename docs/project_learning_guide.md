# AuditPilot M0 项目学习导览：从零理解这个前后端 Demo

这份文档是给“第一次认真掌控一个前后端项目”的你看的。

你不需要一次把所有技术都吃透。这个项目当前最重要的事情只有一件：理解一条最小闭环。

```text
前端上传文件
→ 后端接收文件
→ 后端解析 txt/md/csv
→ audit_engine 编排
→ llm_client 返回 mock 或真实 LLM response
→ 前端展示结果
```

你可以把这个项目看成一个“审计合规智能分析系统的骨架”。现在还不是一个完整产品，也不是完整 RAG 系统。它的价值在于：先把前端、后端、接口、文件上传、文件解析、AI 调用边界跑通。后面再一层一层加厚。

---

## 1. 这个项目到底是什么

### 1.1 业务目标

这个项目的业务目标是做一个“审计合规智能分析 demo”。

更具体地说，它希望以后能帮助审计人员做这样的事：

1. 上传待审核材料，例如报销材料、合同材料、审批说明、制度文件摘录。
2. 输入一个审核问题，例如“请判断这份材料是否存在审批流程风险”。
3. 系统读取材料内容。
4. 系统结合制度依据、历史案例、审计规则，生成初步风险提示。
5. 审计人员再人工复核。

注意这里的关键词是“辅助”和“初步”。审计合规场景很严肃，AI 不应该直接给最终审计结论，也不应该编造制度条款。因此当前 prompt 里明确要求：

```text
不要给出最终审计结论或法律结论。
只输出初步风险提示。
如果材料内容不足，请说明“当前材料证据不足”。
不要编造制度名称、条款编号或文件内容。
```

### 1.2 为什么它叫审计合规智能分析 demo

它叫“审计合规智能分析 demo”，是因为它面向的是审计和合规问题，而不是普通聊天。

普通聊天系统只需要回答用户问题。这个项目将来要处理的是：

1. 文件材料。
2. 审核问题。
3. 制度依据。
4. 风险判断。
5. 人工复核建议。

所以它不只是一个聊天框，而是一个“材料上传 + 审核问题 + 分析结果”的业务流程 demo。

当前目录名是：

```text
audit-compliance-demo
```

你可以把它理解为：

```text
audit       审计
compliance  合规
demo        当前只是演示版本
```

### 1.3 当前 M0 版本实现了什么

当前 M0/M0+ 版本实现的是最小可运行闭环。

它已经做到：

1. 前端可以启动 React 页面。
2. 前端可以选择多个文件。
3. 前端可以输入审核问题。
4. 前端点击“开始分析”后，会向后端发送 HTTP 请求。
5. 后端 FastAPI 可以启动。
6. 后端提供 `GET /health`。
7. 后端提供 `POST /api/analyze`。
8. 后端能接收 multipart/form-data 上传。
9. 后端能把上传文件保存到 `backend/uploads/`。
10. 后端能解析 `.txt`、`.md`、`.csv`。
11. 不支持的文件类型会返回 `unsupported`，不会让整个请求崩掉。
12. 后端会调用 `audit_engine.py` 做业务编排。
13. `audit_engine.py` 会拼接 prompt。
14. `llm_client.py` 在没有 `LLM_API_KEY` 时返回 mock response。
15. 如果配置了 API key，`llm_client.py` 会调用 OpenAI-compatible `/chat/completions`。
16. 前端会展示 `answer_text`。
17. 前端会展示 `parsed_files`。
18. 前端会显示 `retrieved_regulations` 的空状态。

### 1.4 当前 M0 版本没有实现什么

当前版本没有实现：

1. PDF 解析。
2. docx 解析。
3. xlsx 解析。
4. ChromaDB。
5. embedding。
6. 制度文档向量化。
7. vector retrieval。
8. 真实制度 RAG。
9. 案例库。
10. 数据库。
11. 登录。
12. 权限。
13. 报告导出。
14. 审计任务管理。
15. 前端复杂交互。

这不是漏做，而是项目切片策略。

### 1.5 为什么当前只是“上传文件 + mock AI 分析”

因为这个项目当前要验证的是端到端链路，而不是 AI 能力本身。

一个完整 RAG 系统至少需要：

1. 文档解析。
2. chunk 切分。
3. embedding 模型。
4. 向量数据库。
5. 检索策略。
6. prompt 编排。
7. LLM 调用。
8. 结果展示。
9. 引用溯源。
10. 错误处理。

如果第一步就同时做这些，初学者会很快失去掌控感，因为你不知道问题出在哪里：

1. 是前端没传文件？
2. 是后端没收到？
3. 是文件解析失败？
4. 是 embedding 失败？
5. 是 ChromaDB 没写进去？
6. 是检索没结果？
7. 是模型接口失败？
8. 是前端没展示？

所以当前版本先把链路缩短成：

```text
上传文件 → 解析基础文本 → mock AI → 展示结果
```

这样你能先掌控“全栈项目的骨架”。

### 1.6 为什么先搭骨架，而不是直接做 ChromaDB / embedding / 制度检索

因为复杂系统要先有边界，再加能力。

当前骨架已经把未来功能的位置留好了：

1. `document_parser.py`：以后扩展 PDF/docx/xlsx。
2. `regulation_indexer.py`：以后扫描制度文件并构建索引。
3. `embedding_client.py`：以后调用 embedding API 或本地 embedding model。
4. `vector_retriever.py`：以后从 ChromaDB 检索制度片段。
5. `audit_engine.py`：以后把上传材料、制度片段、审核问题一起编排进 prompt。
6. `schemas.py`：以后扩展返回结构，例如制度引用、来源文件、分数、元数据。
7. 前端 `retrieved_regulations` 区域：以后展示制度依据。

先搭骨架的好处是：后面每次只改一个模块，不会把整个项目改乱。

### 1.7 当前项目在路线图中的位置

可以把路线图理解成：

```text
M0：跑通前后端闭环
M1：增强文档解析
M2：制度文档 chunk 预处理
M3：embedding + ChromaDB
M4：vector_retriever 检索制度片段
M5：前端展示制度依据
M6：接入更完整的审计业务流程
```

当前项目处在 M0/M0+：

```text
前端上传文件
→ 后端接收文件
→ 后端解析 txt/md/csv
→ audit_engine 编排
→ llm_client 返回 mock 或真实 LLM response
→ 前端展示结果
```

---

## 2. 项目整体文件树解释

### 2.1 当前源码文件树

下面是当前项目的核心源码文件树。这里刻意不展开 `frontend/node_modules/`、`frontend/dist/`、`backend/.venv/`、`__pycache__/`，因为它们是安装依赖或运行验证产生的目录，不是你优先阅读的业务源码。

```text
audit-compliance-demo/
  .gitignore
  README.md

  backend/
    .env.example
    requirements.txt
    uploads/
      .gitkeep
    app/
      __init__.py
      main.py
      config.py
      schemas.py
      prompts/
        audit_prompt.txt
      services/
        __init__.py
        document_parser.py
        audit_engine.py
        llm_client.py
        regulation_indexer.py
        vector_retriever.py
        embedding_client.py

  frontend/
    index.html
    package.json
    package-lock.json
    tsconfig.json
    vite.config.ts
    src/
      main.tsx
      App.tsx
      api.ts
      App.css

  data/
    regulations/
      raw/
        .gitkeep
    indexes/
      chroma/
        regulations/
          .gitkeep
    samples/
      .gitkeep

  docs/
    architecture_v2_demo_vector.md
    api_contract.md
    demo_script.md
    project_learning_guide.md
```

### 2.2 `frontend/` 是什么

`frontend/` 是前端项目目录。

前端就是用户在浏览器里看到、点击、输入的部分。这个项目的前端使用：

```text
React + Vite + TypeScript
```

它负责：

1. 显示页面。
2. 提供文件选择框。
3. 提供审核问题输入框。
4. 提供“开始分析”按钮。
5. 点击按钮时调用后端 API。
6. 把后端返回的 JSON 展示出来。

### 2.3 `backend/` 是什么

`backend/` 是后端项目目录。

后端就是运行在服务器上的程序。当前使用：

```text
FastAPI + Python
```

它负责：

1. 接收前端请求。
2. 接收上传文件。
3. 保存上传文件。
4. 解析文件。
5. 调用审计分析编排逻辑。
6. 调用 LLM 或返回 mock。
7. 把结果以 JSON 返回给前端。

### 2.4 `data/` 是什么

`data/` 是未来放数据和索引的目录。

当前 M0 版本基本不会使用它，但它已经把未来位置留好：

```text
data/regulations/raw/
data/indexes/chroma/regulations/
data/samples/
```

这是一种项目设计习惯：未来会用到的“数据边界”先摆出来，但不急着实现功能。

### 2.5 `docs/` 是什么

`docs/` 是项目文档目录。

当前已有：

1. `architecture_v2_demo_vector.md`：架构说明。
2. `api_contract.md`：API 契约。
3. `demo_script.md`：演示脚本。
4. `project_learning_guide.md`：你现在正在看的学习导览。

文档的作用是让你逐步建立掌控感，不需要每次都从代码里反推整个系统。

### 2.6 `backend/app/services/` 是什么

`backend/app/services/` 是后端服务模块目录。

你可以把它理解为“后端功能组件”的集合。

当前里面有：

1. `document_parser.py`：负责解析上传文件。
2. `audit_engine.py`：负责审计业务编排。
3. `llm_client.py`：负责调用 LLM 或返回 mock。
4. `regulation_indexer.py`：未来负责制度文档索引。
5. `vector_retriever.py`：未来负责制度片段检索。
6. `embedding_client.py`：未来负责 embedding。

为什么不把所有代码都写在 `main.py`？

因为 `main.py` 应该主要负责 API 入口。如果把解析、模型调用、制度检索都塞进去，后面会变成一个巨大的混乱文件。拆成 services 以后，每个文件职责更清楚。

### 2.7 `backend/uploads/` 是什么

`backend/uploads/` 是后端保存用户上传文件的地方。

当用户上传 `example.txt` 时，后端不会直接用原名保存，而是会生成类似：

```text
uuid_example.txt
```

这样做是为了减少重名冲突，也避免用户上传的文件名影响服务器路径。

当前 `.gitignore` 里忽略了：

```text
backend/uploads/*
!backend/uploads/.gitkeep
```

意思是：

1. 上传文件不要提交到 git。
2. 但保留 `.gitkeep`，让空目录也能被保留。

### 2.8 `data/regulations/raw/` 未来做什么

`data/regulations/raw/` 未来用来放原始制度文件。

例如：

```text
data/regulations/raw/
  财务报销管理办法.pdf
  合同审批制度.docx
  采购管理制度.md
```

未来 `regulation_indexer.py` 会扫描这个目录，把制度文件解析、切 chunk、做 embedding，然后写入 ChromaDB。

当前 M0 不做这些。

### 2.9 `data/indexes/chroma/regulations/` 未来做什么

`data/indexes/chroma/regulations/` 未来用来存 ChromaDB 的制度向量索引。

简单说：

1. 原始制度文件在 `data/regulations/raw/`。
2. 程序把制度文件切成小片段。
3. 每个片段转成向量。
4. 向量写入 ChromaDB。
5. ChromaDB 的持久化数据将来可以放在 `data/indexes/chroma/regulations/`。

当前 M0 只是创建目录，没有实现 ChromaDB。

---

## 3. 前端和后端的关系

### 3.1 什么是前端

前端就是用户在浏览器里看到的界面。

在这个项目里，前端是：

```text
frontend/
```

它使用 React 写页面，用 Vite 启动开发服务器。用户看到的文件选择框、textarea、按钮、结果区域，都是前端。

### 3.2 什么是后端

后端就是运行在服务器上的程序。

在这个项目里，后端是：

```text
backend/
```

它使用 FastAPI 写接口。前端不能直接读取服务器文件，也不能直接调用 Python 函数。它需要通过 HTTP 请求调用后端 API。

### 3.3 浏览器里看到的是前端

当你打开：

```text
http://127.0.0.1:5173/
```

浏览器加载的是 Vite 提供的 React 前端页面。

你在页面上：

1. 选择文件。
2. 输入审核问题。
3. 点击“开始分析”。

这些动作首先都发生在浏览器里的前端代码中。

### 3.4 FastAPI 跑的是后端

当你启动：

```bash
fastapi dev app/main.py
```

运行的是 Python 后端。

后端默认监听：

```text
http://127.0.0.1:8000/
```

它提供：

```text
GET  /health
POST /api/analyze
```

### 3.5 前端如何通过 HTTP 请求调用后端

前端通过 `fetch()` 调用后端。

当前代码在 `frontend/src/api.ts`：

```typescript
const response = await fetch("/api/analyze", {
  method: "POST",
  body: formData
});
```

这里的 `/api/analyze` 是一个相对路径。开发时 Vite 会根据 `frontend/vite.config.ts` 里的 proxy 配置，把它转发给后端：

```typescript
proxy: {
  "/api": "http://localhost:8000",
  "/health": "http://localhost:8000"
}
```

所以浏览器请求：

```text
http://127.0.0.1:5173/api/analyze
```

Vite dev server 会转发到：

```text
http://localhost:8000/api/analyze
```

### 3.6 为什么前端地址通常是 `http://127.0.0.1:5173/`

因为 Vite 的开发服务器默认常用 5173 端口。

当前 `frontend/vite.config.ts` 明确写了：

```typescript
server: {
  port: 5173
}
```

所以前端启动后，一般打开：

```text
http://127.0.0.1:5173/
```

或者：

```text
http://localhost:5173/
```

### 3.7 为什么后端地址通常是 `http://127.0.0.1:8000/`

因为 FastAPI/Uvicorn 开发服务器默认常用 8000 端口。

启动后端：

```bash
fastapi dev app/main.py
```

通常会看到类似：

```text
Server started at http://127.0.0.1:8000
Documentation at http://127.0.0.1:8000/docs
```

### 3.8 什么是 API

API 可以理解成“前端和后端约定好的接口”。

比如后端说：

```text
你可以 POST /api/analyze
给我 files 和 question
我会返回 answer_text、parsed_files、retrieved_regulations
```

这就是 API 契约。

前端不需要知道后端内部怎么解析文件，也不需要知道 LLM 怎么调用。前端只需要遵守这个 API 契约。

### 3.9 什么是 CORS

CORS 是浏览器的安全机制，全称是 Cross-Origin Resource Sharing。

如果前端页面在：

```text
http://127.0.0.1:5173
```

后端接口在：

```text
http://127.0.0.1:8000
```

它们端口不同，浏览器会认为这是不同 origin。浏览器会限制跨域请求，除非后端明确允许。

当前后端在 `backend/app/main.py` 中配置了：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

意思是：允许来自前端开发地址的浏览器请求访问后端。

### 3.10 为什么前端和后端可以分开启动

因为它们是两个独立进程：

1. 前端 Vite server 负责提供网页。
2. 后端 FastAPI server 负责提供 API。

它们之间通过 HTTP 通信，而不是互相 import 对方代码。

这也是现代全栈项目常见结构：

```text
浏览器跑前端
服务器跑后端
HTTP 连接两者
```

### 3.11 文字版流程图

```text
用户浏览器
  ↓
React 前端页面
  ↓ fetch()
FastAPI 后端接口 /api/analyze
  ↓
后端保存文件、解析文件、调用 audit_engine
  ↓
返回 JSON
  ↓
React 前端展示结果
```

---

## 4. 启动项目的完整流程

### 4.1 启动后端

从零启动后端：

```bash
cd /home/spark/workspace/audit-compliance-demo/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
fastapi dev app/main.py
```

### 4.2 `cd backend` 是什么

`cd` 是 change directory，意思是切换当前目录。

后端命令要在 `backend/` 目录里执行，因为：

1. `requirements.txt` 在 `backend/`。
2. `.env` 默认也会在 `backend/`。
3. `app/main.py` 是相对 `backend/` 的路径。

如果你站在项目根目录，也可以写完整路径：

```bash
cd /home/spark/workspace/audit-compliance-demo/backend
```

### 4.3 `python -m venv .venv` 是什么

这条命令创建 Python 虚拟环境。

```bash
python -m venv .venv
```

含义是：

1. 用当前 Python 创建一个隔离环境。
2. 环境目录叫 `.venv`。
3. 后面安装的 Python 依赖会放进 `.venv`，不会污染系统 Python。

### 4.4 为什么要虚拟环境

因为不同项目可能需要不同版本的依赖。

例如：

1. 这个项目用 FastAPI。
2. 另一个项目可能用 Flask。
3. 一个项目需要 httpx 0.28。
4. 另一个项目需要 httpx 旧版本。

如果都装在系统 Python 里，很容易互相影响。虚拟环境让每个项目有自己的依赖空间。

### 4.5 `source .venv/bin/activate` 是什么

这条命令激活虚拟环境。

```bash
source .venv/bin/activate
```

激活后，你终端里的 `python`、`pip` 通常会指向：

```text
backend/.venv/bin/python
backend/.venv/bin/pip
```

你会经常看到命令行前面出现：

```text
(.venv)
```

这说明虚拟环境已经启用。

### 4.6 `pip install -r requirements.txt` 是什么

这条命令安装后端依赖。

```bash
pip install -r requirements.txt
```

`requirements.txt` 当前内容是：

```text
fastapi[standard]
pydantic-settings
python-multipart
httpx
```

它们分别大致负责：

1. `fastapi[standard]`：FastAPI 框架和标准开发运行工具。
2. `pydantic-settings`：从 `.env` 读取配置。
3. `python-multipart`：支持 multipart/form-data 文件上传。
4. `httpx`：后端调用 LLM API 时发送 HTTP 请求。

### 4.7 `fastapi dev app/main.py` 是什么

这条命令启动 FastAPI 开发服务器。

```bash
fastapi dev app/main.py
```

它会：

1. 找到 `app/main.py`。
2. 找到里面的 `app = FastAPI(...)`。
3. 启动开发服务器。
4. 监听 8000 端口。
5. 开启开发模式的自动重载。

### 4.8 后端启动后应该看到什么

通常会看到类似：

```text
FastAPI Starting development server
Server started at http://127.0.0.1:8000
Documentation at http://127.0.0.1:8000/docs
Uvicorn running on http://127.0.0.1:8000
```

如果你看到这些，说明后端起来了。

### 4.9 如何访问 `/health`

浏览器打开：

```text
http://127.0.0.1:8000/health
```

或者用 curl：

```bash
curl http://127.0.0.1:8000/health
```

应该返回：

```json
{
  "status": "ok"
}
```

### 4.10 启动前端

从零启动前端：

```bash
cd /home/spark/workspace/audit-compliance-demo/frontend
npm install
npm run dev
```

### 4.11 `npm install` 是什么

`npm install` 会读取 `frontend/package.json`，安装前端依赖。

当前依赖包括：

1. `react`
2. `react-dom`
3. `lucide-react`
4. `vite`
5. `typescript`
6. React 类型定义

安装后会生成：

```text
frontend/node_modules/
frontend/package-lock.json
```

`node_modules/` 是依赖目录，通常很大，不要手动阅读，也不要提交到 git。

### 4.12 `npm run dev` 是什么

`npm run dev` 会执行 `package.json` 里的脚本：

```json
"dev": "vite"
```

也就是启动 Vite 开发服务器。

### 4.13 Vite dev server 是什么

Vite dev server 是前端开发服务器。

它负责：

1. 提供 `index.html`。
2. 编译 TypeScript/React。
3. 支持热更新。
4. 把 `/api` 请求代理到后端。

启动后通常会看到：

```text
VITE ready
Local: http://127.0.0.1:5173/
```

### 4.14 如何打开前端页面

打开：

```text
http://127.0.0.1:5173/
```

你会看到一个单页应用：

1. 左侧上传文件和输入问题。
2. 右侧展示 AI 初步审核意见、文件解析状态、制度引用片段空状态。

### 4.15 前端页面和后端接口如何配合

前端页面本身不会解析文件，也不会调用 LLM。

它点击“开始分析”后：

1. 把文件和问题打包成 `FormData`。
2. 通过 `fetch("/api/analyze")` 发给后端。
3. 后端处理完返回 JSON。
4. 前端把 JSON 存进 React state。
5. 页面自动显示新结果。

---

## 5. 后端代码逐文件讲解

### 5.1 `backend/app/main.py`

#### 职责

`main.py` 是后端入口文件。

它负责：

1. 创建 FastAPI app。
2. 配置 CORS。
3. 定义 `/health`。
4. 定义 `/api/analyze`。
5. 保存上传文件。
6. 调用 `DocumentParser`。
7. 调用 `AuditEngine`。
8. 返回 `AnalyzeResponse`。

#### 它被谁调用

它被 FastAPI 开发服务器调用。

启动命令：

```bash
fastapi dev app/main.py
```

FastAPI 会加载：

```python
app = FastAPI(title="Audit Compliance Demo API")
```

#### 它调用了谁

`main.py` 调用了：

1. `get_settings()`：来自 `config.py`。
2. `AnalyzeResponse`：来自 `schemas.py`。
3. `DocumentParser`：来自 `document_parser.py`。
4. `LLMClient`：来自 `llm_client.py`。
5. `AuditEngine`：来自 `audit_engine.py`。

#### 重要变量

```python
BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "uploads"
PROMPT_PATH = BASE_DIR / "app" / "prompts" / "audit_prompt.txt"
```

含义：

1. `BASE_DIR` 指向 `backend/`。
2. `UPLOAD_DIR` 指向 `backend/uploads/`。
3. `PROMPT_PATH` 指向 prompt 文件。

#### 重要函数

```python
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

这是健康检查接口。

```python
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(...)
```

这是分析接口。

#### 初学者重点看哪里

优先看：

1. `app = FastAPI(...)`
2. `app.add_middleware(CORSMiddleware, ...)`
3. `@app.get("/health")`
4. `@app.post("/api/analyze")`
5. `for upload in files:`
6. `saved_path.write_bytes(content)`
7. `parser.parse(saved_path, safe_name)`
8. `audit_engine.analyze(...)`

#### 未来如何扩展

未来可能会：

1. 增加制度索引接口。
2. 增加上传样例文件接口。
3. 增加 RAG 检索调用。
4. 增加任务 ID。
5. 增加日志。

但 M0 阶段不需要改它太多。

### 5.2 `backend/app/config.py`

#### 职责

`config.py` 负责读取配置。

当前配置项：

```python
llm_base_url: str
llm_api_key: str
llm_model: str
```

#### 它被谁调用

它被 `main.py` 调用：

```python
settings = get_settings()
```

#### 它调用了谁

它使用：

```python
pydantic_settings.BaseSettings
```

从环境变量和 `.env` 中读取配置。

#### 重要类和函数

```python
class Settings(BaseSettings):
    llm_base_url: str = "http://your-qwen-api-server/v1"
    llm_api_key: str = ""
    llm_model: str = "qwen3"
```

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

`@lru_cache` 的意思是：配置读取一次后缓存起来，不用每次请求都重新读取。

#### 初学者重点看哪里

重点看：

1. `Settings` 里有哪些字段。
2. `env_file=".env"`。
3. `get_settings()`。

#### 未来如何扩展

未来可能加入：

1. embedding API key。
2. ChromaDB 路径。
3. 上传文件大小限制。
4. 模型温度参数。
5. 是否启用 mock 模式。

### 5.3 `backend/app/schemas.py`

#### 职责

`schemas.py` 定义后端数据结构，也就是 API 的数据契约。

当前有：

```python
ParsedFileSummary
RegulationChunk
AnalyzeResponse
```

#### 它被谁调用

它被这些文件调用：

1. `main.py`
2. `document_parser.py`
3. `audit_engine.py`
4. `vector_retriever.py`

#### 它调用了谁

它使用 Pydantic：

```python
from pydantic import BaseModel, Field
```

#### 重要类

```python
class ParsedFileSummary(BaseModel):
    filename: str
    status: str
    preview: str
    error: str | None = None
```

表示一个上传文件的解析摘要。

```python
class RegulationChunk(BaseModel):
    chunk_id: str
    source_file: str
    content: str
    score: float | None = None
    metadata: dict = Field(default_factory=dict)
```

表示未来检索到的一段制度内容。

```python
class AnalyzeResponse(BaseModel):
    answer_text: str
    parsed_files: list[ParsedFileSummary]
    retrieved_regulations: list[RegulationChunk]
```

表示 `/api/analyze` 的完整返回值。

#### 初学者重点看哪里

重点看这三个类的字段名，因为它们会直接变成前端拿到的 JSON 字段名。

#### 未来如何扩展

未来可能增加：

1. `request_id`
2. `created_at`
3. `risk_level`
4. `citations`
5. `source_page`
6. `chunk_metadata`

### 5.4 `backend/app/services/document_parser.py`

#### 职责

`document_parser.py` 负责解析上传文件。

当前只支持：

```text
.txt
.md
.csv
```

其他格式返回：

```text
unsupported
```

#### 它被谁调用

它被 `main.py` 调用：

```python
parser = DocumentParser()
parsed_files.append(parser.parse(saved_path, safe_name))
```

#### 它调用了谁

它调用：

1. Python 标准库 `csv`。
2. Python 标准库 `pathlib.Path`。
3. `ParsedFileSummary` schema。

#### 重要类和函数

```python
class DocumentParser:
    supported_suffixes = {".txt", ".md", ".csv"}
```

表示当前支持的后缀。

```python
def parse(self, file_path: Path, original_filename: str) -> ParsedFileSummary:
```

这是当前解析入口。

如果后缀不支持：

```python
return ParsedFileSummary(
    filename=original_filename,
    status="unsupported",
    preview="",
    error=f"Unsupported file type: {suffix or 'unknown'}",
)
```

如果是 `.csv`：

```python
content = self._read_csv_preview(file_path)
```

如果是 `.txt` 或 `.md`：

```python
content = file_path.read_text(encoding="utf-8", errors="replace")
```

如果解析异常：

```python
status="failed"
```

#### 初学者重点看哪里

重点看：

1. `supported_suffixes`
2. `parse()`
3. `_read_csv_preview()`
4. `_preview()`

#### 未来如何扩展

未来 PDF/docx/xlsx 解析会主要改这里。

例如：

1. PDF：可能用 `pypdf` 或 `pdfplumber`。
2. docx：可能用 `python-docx`。
3. xlsx：可能用 `openpyxl`。

但这些都属于后续 Slice 1，不是当前 M0。

### 5.5 `backend/app/services/audit_engine.py`

#### 职责

`audit_engine.py` 是当前后端的业务编排者。

它负责：

1. 接收用户问题。
2. 接收解析后的文件摘要。
3. 读取 prompt 模板。
4. 拼接完整 prompt。
5. 调用 `LLMClient`。
6. 组装 `AnalyzeResponse`。

它不直接解析文件，也不直接发送 HTTP 请求。它的重点是“审计分析业务流程”。

#### 它被谁调用

它被 `main.py` 调用：

```python
audit_engine = AuditEngine(llm_client=llm_client, prompt_path=PROMPT_PATH)
return await audit_engine.analyze(question=question, parsed_files=parsed_files)
```

#### 它调用了谁

它调用：

1. `LLMClient.chat_completion()`
2. `AnalyzeResponse`
3. `ParsedFileSummary`

#### 重要类和函数

```python
class AuditEngine:
```

核心业务编排类。

```python
async def analyze(...)
```

分析入口。

```python
def _build_prompt(...)
```

把 prompt 模板、用户问题、文件解析结果拼成完整 prompt。

#### 初学者重点看哪里

重点看：

1. `self.prompt_template = prompt_path.read_text(...)`
2. `prompt = self._build_prompt(question, parsed_files)`
3. `answer_text = await self.llm_client.chat_completion(prompt)`
4. `retrieved_regulations=[]`

最后一行非常重要：当前制度检索还没有接入，所以这里返回空数组。

#### 未来如何扩展

未来会在这里接入：

1. `VectorRetriever`
2. 检索到的制度片段
3. 更复杂的 prompt 拼接
4. 风险等级结构化输出

### 5.6 `backend/app/services/llm_client.py`

#### 职责

`llm_client.py` 只负责模型调用。

它不应该知道审计业务细节。它只做：

1. 判断有没有 API key。
2. 没有 API key 时返回 mock。
3. 有 API key 时调用 `/chat/completions`。
4. 返回模型输出文本。

#### 它被谁调用

它被 `audit_engine.py` 调用：

```python
answer_text = await self.llm_client.chat_completion(prompt)
```

它也在 `main.py` 中被创建：

```python
llm_client = LLMClient(settings)
```

#### 它调用了谁

它调用：

1. `httpx.AsyncClient`
2. OpenAI-compatible LLM API

#### 重要类和函数

```python
class LLMClient:
```

```python
async def chat_completion(self, prompt: str) -> str:
```

这是对外入口。

如果没有 API key：

```python
if not self.settings.llm_api_key:
    return self._mock_response(prompt)
```

如果有 API key：

```python
url = f"{base_url}/chat/completions"
```

然后发送：

```python
response = await client.post(url, json=payload, headers=headers)
```

#### 初学者重点看哪里

重点看：

1. `if not self.settings.llm_api_key`
2. `_mock_response()`
3. `url = f"{base_url}/chat/completions"`
4. `payload`
5. `headers`
6. `return data["choices"][0]["message"]["content"]`

#### 未来如何扩展

未来可能增加：

1. 错误重试。
2. 超时配置。
3. 流式输出。
4. 模型切换。
5. token 统计。
6. 结构化 JSON 输出。

### 5.7 `backend/app/services/regulation_indexer.py`

#### 职责

这是未来制度索引模块。

当前只是占位：

```python
class RegulationIndexer:
    """Placeholder for future regulation indexing."""
```

#### 它被谁调用

当前没有被业务流程调用。

#### 它调用了谁

当前没有实际调用。

#### 重要函数

```python
def build_index(self) -> None:
```

当前会抛出：

```python
NotImplementedError
```

#### 初学者重点看哪里

重点理解：这是未来放“制度文件索引逻辑”的地方，不是当前 M0 链路的一部分。

#### 未来如何扩展

未来它会：

1. 扫描 `data/regulations/raw/`。
2. 解析制度文件。
3. 切 chunk。
4. 调用 embedding。
5. 写入 ChromaDB。

### 5.8 `backend/app/services/vector_retriever.py`

#### 职责

这是未来向量检索模块。

当前返回空数组：

```python
return []
```

#### 它被谁调用

当前没有被 `audit_engine.py` 调用。

#### 它调用了谁

当前没有调用 ChromaDB。

#### 重要函数

```python
def retrieve(self, query: str, top_k: int = 5) -> list[RegulationChunk]:
```

#### 初学者重点看哪里

重点理解：这个文件未来会根据用户问题，从制度向量库里找相关制度片段。

#### 未来如何扩展

未来可能：

1. 读取 ChromaDB。
2. 用 query embedding 检索 top_k。
3. 返回 `RegulationChunk` 列表。
4. 让前端展示制度依据。

### 5.9 `backend/app/services/embedding_client.py`

#### 职责

这是未来 embedding 模块。

embedding 是把文本转换成向量的过程。

当前函数：

```python
def embed_texts(self, texts: list[str]) -> list[list[float]]:
```

会抛出：

```python
NotImplementedError
```

#### 它被谁调用

当前没有被调用。

#### 它调用了谁

当前没有调用任何 embedding API 或本地模型。

#### 初学者重点看哪里

知道它是未来“文本转向量”的位置即可。

#### 未来如何扩展

未来可能：

1. 调用 OpenAI-compatible embedding API。
2. 调用本地 embedding model。
3. 批量处理制度 chunks。
4. 给 `regulation_indexer.py` 使用。

### 5.10 `backend/app/prompts/audit_prompt.txt`

#### 职责

这是审计分析 prompt 模板。

它告诉模型：

1. 你是什么角色。
2. 当前系统处于 demo 阶段。
3. 不要给最终结论。
4. 不要编造制度条款。
5. 输出格式是什么。

#### 它被谁调用

它被 `audit_engine.py` 读取：

```python
self.prompt_template = prompt_path.read_text(encoding="utf-8")
```

#### 它调用了谁

它只是文本文件，不调用代码。

#### 初学者重点看哪里

重点看“重要要求”和“输出格式”。

#### 未来如何扩展

未来可能：

1. 加入制度引用格式。
2. 加入风险等级定义。
3. 加入更严格的 JSON 输出格式。
4. 加入证据不足时的处理规则。

### 5.11 `backend/requirements.txt`

#### 职责

定义后端 Python 依赖。

当前内容：

```text
fastapi[standard]
pydantic-settings
python-multipart
httpx
```

#### 它被谁调用

被 pip 调用：

```bash
pip install -r requirements.txt
```

#### 初学者重点看哪里

每次 AI 改代码后，你都要看它有没有改 `requirements.txt`。

因为新增依赖意味着：

1. 运行环境变复杂。
2. 可能引入安全或版本问题。
3. 可能超出当前 slice 范围。

#### 未来如何扩展

Slice 1 做 PDF/docx/xlsx 时，可能会加解析库。

Slice 3 做 ChromaDB 时，可能会加 ChromaDB 相关库。

### 5.12 `backend/.env.example`

#### 职责

这是环境变量示例文件。

当前内容：

```env
LLM_BASE_URL=http://your-qwen-api-server/v1
LLM_API_KEY=
LLM_MODEL=qwen3
```

#### 它被谁调用

它本身不会被自动读取。你需要复制成 `.env`：

```bash
cp .env.example .env
```

然后 `config.py` 会读取 `.env`。

#### 初学者重点看哪里

重点看：

1. `LLM_BASE_URL`
2. `LLM_API_KEY`
3. `LLM_MODEL`

不要把真实 API key 提交到 git。

#### 未来如何扩展

未来可能加入：

1. `EMBEDDING_BASE_URL`
2. `EMBEDDING_API_KEY`
3. `CHROMA_PERSIST_DIR`
4. `ENABLE_MOCK_LLM`

---

## 6. 后端请求生命周期详解

当用户在前端点击“开始分析”时，后端发生的是一串清晰的步骤。

### 6.1 前端把 files 和 question 发到 `/api/analyze`

前端在 `frontend/src/api.ts` 中创建 `FormData`：

```typescript
const formData = new FormData();
files.forEach((file) => formData.append("files", file));
formData.append("question", question);
```

然后发送：

```typescript
fetch("/api/analyze", {
  method: "POST",
  body: formData
})
```

### 6.2 `main.py` 的 `/api/analyze` endpoint 接收到请求

后端入口是：

```python
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    files: list[UploadFile] = File(default=[]),
    question: str = Form(...),
) -> AnalyzeResponse:
```

FastAPI 会自动把 multipart/form-data 解析成：

1. `files`: `UploadFile` 列表。
2. `question`: 字符串。

### 6.3 后端为每个上传文件生成安全文件名

当前代码：

```python
safe_name = Path(upload.filename or "uploaded_file").name
saved_name = f"{uuid4().hex}_{safe_name}"
saved_path = UPLOAD_DIR / saved_name
```

这里做了两件事：

1. `Path(...).name`：只保留文件名，避免用户传入奇怪路径。
2. `uuid4().hex`：加随机前缀，避免重名覆盖。

### 6.4 后端把文件保存到 `backend/uploads/`

当前代码：

```python
content = await upload.read()
saved_path.write_bytes(content)
```

意思是：

1. 从请求里读取上传文件内容。
2. 写到服务器本地磁盘。

保存目录是：

```text
backend/uploads/
```

### 6.5 后端调用 `document_parser.py` 解析文件

当前代码：

```python
parsed_files.append(parser.parse(saved_path, safe_name))
```

注意：当前实际函数名是 `parse()`，不是 `parse_file()`。

### 6.6 `document_parser.py` 返回 parsed / unsupported / failed 状态

如果是 `.txt` 或 `.md`：

```text
status = parsed
```

如果是 `.csv`：

```text
status = parsed
```

如果是不支持格式：

```text
status = unsupported
```

如果读取过程中出错：

```text
status = failed
```

返回结构都是 `ParsedFileSummary`。

### 6.7 解析结果传入业务编排

`main.py` 创建：

```python
llm_client = LLMClient(settings)
audit_engine = AuditEngine(llm_client=llm_client, prompt_path=PROMPT_PATH)
```

然后调用：

```python
return await audit_engine.analyze(question=question, parsed_files=parsed_files)
```

### 6.8 `audit_engine.py` 读取 prompt

在 `AuditEngine.__init__()` 中：

```python
self.prompt_template = prompt_path.read_text(encoding="utf-8")
```

读取的是：

```text
backend/app/prompts/audit_prompt.txt
```

### 6.9 `audit_engine.py` 调用 `llm_client.py`

在 `AuditEngine.analyze()` 中：

```python
prompt = self._build_prompt(question, parsed_files)
answer_text = await self.llm_client.chat_completion(prompt)
```

它先拼 prompt，再交给 LLM client。

### 6.10 `llm_client.py` 如果没有 API key，返回 mock response

当前逻辑：

```python
if not self.settings.llm_api_key:
    return self._mock_response(prompt)
```

所以只要你没有配置 `LLM_API_KEY`，系统不会报错，而是返回固定 mock。

### 6.11 后端组装 `AnalyzeResponse`

在 `audit_engine.py` 中：

```python
return AnalyzeResponse(
    answer_text=answer_text,
    parsed_files=parsed_files,
    retrieved_regulations=[],
)
```

当前 `retrieved_regulations` 是空数组，因为还没有接入制度检索。

### 6.12 FastAPI 自动把 Python 对象变成 JSON 返回给前端

因为 endpoint 声明了：

```python
response_model=AnalyzeResponse
```

FastAPI 会把 Pydantic model 转成 JSON。

前端收到的就是：

```json
{
  "answer_text": "...",
  "parsed_files": [...],
  "retrieved_regulations": []
}
```

### 6.13 后端生命周期流程图

```text
POST /api/analyze
  ↓
main.py
  ↓
保存上传文件
  ↓
document_parser.parse()
  ↓
audit_engine.analyze()
  ↓
llm_client.chat_completion()
  ↓
AnalyzeResponse
  ↓
JSON response
```

---

## 7. API 契约详解

当前后端有两个 API。

### 7.1 `GET /health`

#### 用来干什么

`/health` 用来确认后端是否启动成功。

它不做业务分析，不需要文件，也不需要 API key。

#### 请求方式是什么

请求方式是：

```text
GET
```

GET 通常用于读取信息，不改变服务器状态。

#### 返回什么

返回：

```json
{
  "status": "ok"
}
```

#### 如何用浏览器测试

打开：

```text
http://127.0.0.1:8000/health
```

#### 如何用 curl 测试

```bash
curl http://127.0.0.1:8000/health
```

返回：

```json
{
  "status": "ok"
}
```

### 7.2 `POST /api/analyze`

#### 用来干什么

`/api/analyze` 用来提交上传文件和审核问题，让后端返回初步分析结果。

#### 为什么是 POST

因为它不是简单读取资源，而是提交数据给后端处理。

它会：

1. 上传文件。
2. 保存文件。
3. 解析文件。
4. 调用分析逻辑。

这些都属于“提交处理”，所以用 POST。

#### 为什么用 multipart/form-data

因为请求里包含文件。

JSON 很适合传文本、数字、数组、对象，但不适合直接传浏览器里的 File 对象。文件上传通常使用：

```text
multipart/form-data
```

它可以同时传：

1. 文件字段。
2. 普通文本字段。

#### `files` 字段是什么

`files` 是上传文件列表。

后端接收方式：

```python
files: list[UploadFile] = File(default=[])
```

前端添加方式：

```typescript
files.forEach((file) => formData.append("files", file));
```

注意：多个文件使用同一个字段名 `files` 重复 append。

#### `question` 字段是什么

`question` 是用户输入的审核问题。

例如：

```text
请对这份材料做初步审计分析
```

后端接收方式：

```python
question: str = Form(...)
```

#### 返回 JSON 的结构是什么

返回结构：

```json
{
  "answer_text": "AI 初步审核意见或 mock response",
  "parsed_files": [
    {
      "filename": "example.txt",
      "status": "parsed",
      "preview": "文件内容预览...",
      "error": null
    }
  ],
  "retrieved_regulations": []
}
```

#### `answer_text` 是什么

`answer_text` 是 AI 或 mock 返回的分析文本。

当前没有 API key 时，它来自：

```python
LLMClient._mock_response()
```

#### `parsed_files` 是什么

`parsed_files` 是每个上传文件的解析摘要。

每一项包括：

1. `filename`：原始文件名。
2. `status`：`parsed` / `unsupported` / `failed`。
3. `preview`：内容预览。
4. `error`：错误信息，没有错误时为 null。

#### `retrieved_regulations` 为什么现在是空数组

因为当前 M0 没有接入 ChromaDB、embedding、制度检索。

但返回结构里先保留这个字段，是为了未来接入 RAG 后不用大改前端和 API 契约。

#### curl 示例

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -F "question=请对这份材料做初步审计分析" \
  -F "files=@/path/to/example.txt"
```

逐段解释：

```bash
curl
```

命令行 HTTP 工具。

```bash
-X POST
```

指定请求方式是 POST。

```bash
http://127.0.0.1:8000/api/analyze
```

后端分析接口地址。

```bash
-F "question=请对这份材料做初步审计分析"
```

以 multipart/form-data 形式提交文本字段 `question`。

```bash
-F "files=@/path/to/example.txt"
```

上传一个文件，字段名是 `files`，`@` 后面是本地文件路径。

如果上传多个文件，可以写多个 `-F files=@...`：

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -F "question=请对这些材料做初步审计分析" \
  -F "files=@/path/to/a.txt" \
  -F "files=@/path/to/b.md"
```

---

## 8. `schemas.py` 的意义

### 8.1 为什么要有 `schemas.py`

`schemas.py` 是前后端数据结构的“契约中心”。

如果没有它，后端可能随手返回：

```python
return {"text": "..."}
```

下一次又返回：

```python
return {"answer": "...", "files": "..."}
```

前端就不知道该读哪个字段。

有了 `schemas.py`，后端明确承诺 `/api/analyze` 返回：

```text
answer_text
parsed_files
retrieved_regulations
```

### 8.2 什么是 Pydantic model

Pydantic model 是 Python 里的数据模型。

例如：

```python
class ParsedFileSummary(BaseModel):
    filename: str
    status: str
    preview: str
    error: str | None = None
```

它表达的是：

1. `filename` 必须是字符串。
2. `status` 必须是字符串。
3. `preview` 必须是字符串。
4. `error` 可以是字符串，也可以是 None。

Pydantic 会帮你做数据校验和 JSON 转换。

### 8.3 为什么 API 返回值不直接用 dict

直接用 dict 可以跑，但长期不稳。

比如：

```python
return {
    "answer_text": answer_text,
    "parsed_files": parsed_files,
    "retrieved_regulations": [],
}
```

这看起来简单，但没有类型保护。

用 Pydantic model 的好处：

1. 字段清晰。
2. 类型清晰。
3. 自动生成 OpenAPI 文档。
4. 前端更容易对齐类型。
5. 未来扩展更可控。

### 8.4 `ParsedFileSummary` 的作用

它描述一个文件的解析结果：

```text
filename: 文件名
status: 解析状态
preview: 内容预览
error: 错误信息
```

前端“文件解析状态”区域展示的就是它。

### 8.5 `RegulationChunk` 的作用

它描述未来检索到的一段制度文本：

```text
chunk_id: 片段 ID
source_file: 来源制度文件
content: 片段内容
score: 检索相关性分数
metadata: 额外元数据
```

当前没有真实数据，所以 `retrieved_regulations` 是空数组。

### 8.6 `AnalyzeResponse` 的作用

它描述 `/api/analyze` 的完整响应：

```text
answer_text
parsed_files
retrieved_regulations
```

这就是前端最终消费的数据结构。

### 8.7 前后端为什么需要统一的数据结构

前端和后端是两个独立程序。它们通过 JSON 通信。

如果后端返回：

```json
{
  "answer_text": "..."
}
```

前端就应该读：

```typescript
result.answer_text
```

如果后端改成：

```json
{
  "answer": "..."
}
```

前端还读 `result.answer_text`，页面就会空掉。

所以数据结构必须统一。

### 8.8 什么是“数据契约”

数据契约就是双方约定：

```text
你给我什么字段
我返回什么字段
每个字段是什么类型
哪些字段一定有
哪些字段可以为空
```

在这个项目中：

1. 后端用 `schemas.py` 定义契约。
2. 前端用 `api.ts` 里的 TypeScript type 对齐契约。

### 8.9 未来接入 ChromaDB 后，`retrieved_regulations` 会如何被填充

未来流程可能是：

1. 用户提交 question。
2. `audit_engine.py` 调用 `vector_retriever.py`。
3. `vector_retriever.py` 从 ChromaDB 检索相关制度片段。
4. 每个片段转成 `RegulationChunk`。
5. `AnalyzeResponse.retrieved_regulations` 返回这些片段。
6. 前端展示来源制度、片段内容和相关分数。

---

## 9. 前端代码逐文件讲解

### 9.1 `frontend/src/App.tsx`

#### 职责

`App.tsx` 是当前前端主页面。

它负责：

1. 保存页面状态。
2. 渲染上传区域。
3. 渲染审核问题输入框。
4. 渲染开始分析按钮。
5. 处理文件选择。
6. 处理表单提交。
7. 调用 `api.ts`。
8. 展示后端返回结果。
9. 展示 loading 和 error 状态。

#### 它和其他文件的关系

它被 `main.tsx` 渲染。

它调用：

```typescript
import { AnalyzeResponse, analyzeFiles } from "./api";
```

它使用样式：

```typescript
import "./App.css";
```

这个样式是在 `main.tsx` 里引入的。

#### 初学者应该先看哪部分

先看 state：

```typescript
const [files, setFiles] = useState<File[]>([]);
const [question, setQuestion] = useState(defaultQuestion);
const [result, setResult] = useState<AnalyzeResponse | null>(null);
const [error, setError] = useState("");
const [loading, setLoading] = useState(false);
```

再看两个函数：

```typescript
function handleFileChange(...)
async function handleSubmit(...)
```

最后看 JSX 里如何展示：

```typescript
result.answer_text
result.parsed_files
result.retrieved_regulations
```

#### 哪些代码负责上传文件

文件选择 input：

```tsx
<input
  id="files"
  type="file"
  multiple
  accept=".txt,.md,.csv"
  onChange={handleFileChange}
/>
```

文件变化处理：

```typescript
function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
  setFiles(Array.from(event.target.files ?? []));
  setResult(null);
  setError("");
}
```

#### 哪些代码负责调用后端

在 `handleSubmit()` 中：

```typescript
const response = await analyzeFiles(files, question.trim());
setResult(response);
```

真正的 HTTP 请求在 `api.ts`。

#### 哪些代码负责展示结果

展示 AI 结果：

```tsx
<pre className="answer-text">{result.answer_text}</pre>
```

展示解析文件：

```tsx
{result.parsed_files.map((file) => (...))}
```

展示制度片段：

```tsx
{result.retrieved_regulations.map((chunk) => (...))}
```

当前制度片段通常为空，所以显示：

```text
当前 M0+ 暂未接入制度检索
```

#### 哪些代码负责 loading 和 error 状态

loading：

```typescript
setLoading(true);
...
setLoading(false);
```

按钮 disabled：

```tsx
<button type="submit" disabled={loading} className="primary-button">
```

按钮文字：

```tsx
{loading ? "正在分析..." : "开始分析"}
```

error：

```typescript
setError(...)
```

展示错误：

```tsx
{error && <div className="error-box">{error}</div>}
```

### 9.2 `frontend/src/api.ts`

#### 职责

`api.ts` 专门负责前端和后端 API 通信。

它定义了：

1. 前端用的 TypeScript 类型。
2. `analyzeFiles()` 请求函数。

#### 它和其他文件的关系

它被 `App.tsx` 调用：

```typescript
import { AnalyzeResponse, analyzeFiles } from "./api";
```

#### 初学者应该先看哪部分

先看类型：

```typescript
export type AnalyzeResponse = { ... };
```

再看请求函数：

```typescript
export async function analyzeFiles(...)
```

#### 哪些代码负责上传文件

```typescript
const formData = new FormData();
files.forEach((file) => formData.append("files", file));
formData.append("question", question);
```

#### 哪些代码负责调用后端

```typescript
const response = await fetch("/api/analyze", {
  method: "POST",
  body: formData
});
```

#### 哪些代码负责处理错误

```typescript
if (!response.ok) {
  const message = await response.text();
  throw new Error(message || `Analyze request failed with ${response.status}`);
}
```

#### 哪些代码负责使用后端 JSON

```typescript
return response.json();
```

这个 JSON 会回到 `App.tsx` 的：

```typescript
const response = await analyzeFiles(...)
setResult(response)
```

### 9.3 `frontend/src/main.tsx`

#### 职责

`main.tsx` 是 React 前端入口。

它负责把 `App` 挂载到 HTML 页面上。

#### 它和其他文件的关系

`index.html` 里有：

```html
<div id="root"></div>
<script type="module" src="/src/main.tsx"></script>
```

`main.tsx` 找到 `root`：

```typescript
createRoot(document.getElementById("root")!).render(...)
```

然后渲染：

```tsx
<App />
```

#### 初学者应该先看哪部分

重点看：

```typescript
import App from "./App";
import "./App.css";
```

以及：

```typescript
createRoot(...).render(<App />)
```

这说明 `App.tsx` 是页面主体。

### 9.4 `frontend/src/App.css`

#### 职责

`App.css` 负责页面样式。

它定义：

1. 页面整体布局。
2. 左侧输入面板。
3. 右侧结果面板。
4. 按钮样式。
5. loading 动画。
6. 错误提示样式。
7. 文件卡片样式。
8. 移动端响应式布局。

#### 它和其他文件的关系

它在 `main.tsx` 中被引入：

```typescript
import "./App.css";
```

`App.tsx` 使用 className：

```tsx
<main className="app-shell">
```

CSS 里定义：

```css
.app-shell { ... }
```

#### 初学者应该先看哪部分

先看布局类：

1. `.app-shell`
2. `.workspace`
3. `.input-panel`
4. `.result-panel`
5. `.result-grid`

再看状态类：

1. `.error-box`
2. `.primary-button:disabled`
3. `.spin`
4. `.status-parsed`
5. `.status-unsupported`
6. `.status-failed`

### 9.5 `frontend/package.json`

#### 职责

`package.json` 是前端项目配置。

它定义：

1. 项目名。
2. 启动脚本。
3. 构建脚本。
4. 前端依赖。

#### 它和其他文件的关系

执行：

```bash
npm install
```

会读取这里的 dependencies 和 devDependencies。

执行：

```bash
npm run dev
```

会读取：

```json
"dev": "vite"
```

#### 初学者应该先看哪部分

先看：

```json
"scripts": {
  "dev": "vite",
  "build": "tsc && vite build",
  "preview": "vite preview"
}
```

再看 dependencies。

### 9.6 `frontend/vite.config.ts`

#### 职责

`vite.config.ts` 是 Vite 配置文件。

当前配置：

```typescript
server: {
  port: 5173,
  proxy: {
    "/api": "http://localhost:8000",
    "/health": "http://localhost:8000"
  }
}
```

#### 它和其他文件的关系

`api.ts` 请求：

```typescript
fetch("/api/analyze")
```

Vite 根据 proxy 把 `/api/analyze` 转发到：

```text
http://localhost:8000/api/analyze
```

#### 初学者应该先看哪部分

重点看：

1. `port: 5173`
2. `proxy`

这两处解释了为什么前端地址是 5173，以及为什么前端可以用相对路径调用后端。

---

## 10. 前端状态管理解释

### 10.1 当前实现与概念状态的对应关系

用户提到的状态包括：

```typescript
files
question
loading
answerText
parsedFiles
retrievedRegulations
error
```

当前代码中实际 state 是：

```typescript
files
question
result
error
loading
```

也就是说，当前没有单独定义：

```typescript
answerText
parsedFiles
retrievedRegulations
```

它们都放在 `result` 里：

```typescript
result.answer_text
result.parsed_files
result.retrieved_regulations
```

这个设计更简单，适合 M0。

### 10.2 `files`

含义：用户选择的文件数组。

定义：

```typescript
const [files, setFiles] = useState<File[]>([]);
```

用户选择文件时：

```typescript
setFiles(Array.from(event.target.files ?? []));
```

### 10.3 `question`

含义：用户输入的审核问题。

定义：

```typescript
const [question, setQuestion] = useState(defaultQuestion);
```

textarea 改变时：

```tsx
onChange={(event) => setQuestion(event.target.value)}
```

### 10.4 `loading`

含义：当前是否正在请求后端。

定义：

```typescript
const [loading, setLoading] = useState(false);
```

点击开始分析后：

```typescript
setLoading(true);
```

请求结束后：

```typescript
setLoading(false);
```

按钮会根据 loading 禁用：

```tsx
disabled={loading}
```

### 10.5 `answerText`

概念上，`answerText` 是后端返回的分析文本。

当前代码没有单独 state，而是：

```typescript
result?.answer_text
```

展示位置：

```tsx
<pre className="answer-text">{result.answer_text}</pre>
```

### 10.6 `parsedFiles`

概念上，`parsedFiles` 是文件解析状态列表。

当前代码没有单独 state，而是：

```typescript
result?.parsed_files
```

展示位置：

```tsx
result.parsed_files.map((file) => ...)
```

### 10.7 `retrievedRegulations`

概念上，`retrievedRegulations` 是制度检索片段。

当前代码没有单独 state，而是：

```typescript
result?.retrieved_regulations
```

当前总是空数组，因为 M0 没有接入制度检索。

### 10.8 `error`

含义：页面错误信息。

定义：

```typescript
const [error, setError] = useState("");
```

可能出现错误的情况：

1. 没输入问题。
2. 没选择文件。
3. 后端请求失败。

展示：

```tsx
{error && <div className="error-box">{error}</div>}
```

### 10.9 点击“开始分析”前后状态如何变化

点击前：

```text
files: 用户选择的文件
question: 用户输入的问题
loading: false
result: null 或上一次结果
error: ""
```

点击后：

```text
error 清空
result 清空
loading 变成 true
```

请求成功后：

```text
result 变成后端 response
loading 变成 false
```

请求失败后：

```text
error 变成错误信息
loading 变成 false
```

### 10.10 为什么 React 页面会自动刷新显示

React 的核心机制是 state 驱动 UI。

当你调用：

```typescript
setResult(response)
```

React 会重新运行 `App()`，然后根据新的 `result` 生成新的页面。

你不需要手动操作 DOM。

### 10.11 前端状态流程图

概念流程：

```text
用户选择文件
  ↓
setFiles()

用户输入问题
  ↓
setQuestion()

用户点击开始分析
  ↓
setLoading(true)
  ↓
调用 analyzeFiles()
  ↓
收到后端 response
  ↓
setResult(response)
  ↓
页面从 result.answer_text 显示答案
页面从 result.parsed_files 显示解析状态
页面从 result.retrieved_regulations 显示制度片段
  ↓
setLoading(false)
```

如果用用户提到的拆分 state 表达，就是：

```text
收到后端 response
  ↓
setAnswerText(response.answer_text)
setParsedFiles(response.parsed_files)
setRetrievedRegulations(response.retrieved_regulations)
setLoading(false)
```

当前代码只是把这三者合并在 `setResult(response)` 里。

---

## 11. `api.ts` 详解

### 11.1 为什么要单独有 `api.ts`

把 API 调用单独放在 `api.ts` 有几个好处：

1. 页面组件 `App.tsx` 不需要关心 HTTP 细节。
2. 后端接口地址变了，只改 `api.ts` 或 Vite proxy。
3. API 类型集中管理。
4. 后续增加更多接口时更清楚。

如果没有 `api.ts`，所有 fetch 都写在 `App.tsx`，页面会越来越乱。

### 11.2 `fetch()` 是什么

`fetch()` 是浏览器提供的 HTTP 请求函数。

简单例子：

```typescript
const response = await fetch("/api/analyze", {
  method: "POST",
  body: formData
});
```

它的意思是：

1. 向 `/api/analyze` 发请求。
2. 请求方式是 POST。
3. 请求体是 `formData`。
4. 等待后端响应。

### 11.3 `FormData` 是什么

`FormData` 是浏览器提供的一种表单数据对象。

它适合上传文件：

```typescript
const formData = new FormData();
formData.append("files", file);
formData.append("question", question);
```

发送时浏览器会自动把它变成 multipart/form-data。

### 11.4 为什么上传文件不能直接用 JSON

JSON 适合：

```json
{
  "question": "请分析"
}
```

但浏览器里的 `File` 对象不是普通 JSON 字符串。文件包含二进制内容、文件名、类型等信息。

所以文件上传通常用：

```text
multipart/form-data
```

### 11.5 `API_BASE_URL` 是什么

很多前端项目会定义：

```typescript
const API_BASE_URL = "http://127.0.0.1:8000";
```

然后请求：

```typescript
fetch(`${API_BASE_URL}/api/analyze`)
```

但当前项目没有定义 `API_BASE_URL`。

当前项目使用的是相对路径：

```typescript
fetch("/api/analyze")
```

再通过 `vite.config.ts` 里的 proxy 转发到后端。

这种方式在开发阶段很方便，因为前端代码不需要硬编码后端地址。

### 11.6 前端如何处理后端错误

`api.ts` 中：

```typescript
if (!response.ok) {
  const message = await response.text();
  throw new Error(message || `Analyze request failed with ${response.status}`);
}
```

意思是：

1. 如果 HTTP 状态不是 2xx。
2. 读取后端返回的错误文本。
3. 抛出 Error。

`App.tsx` 中：

```typescript
catch (requestError) {
  setError(requestError instanceof Error ? requestError.message : "分析请求失败。");
}
```

把错误显示到页面。

### 11.7 后端返回 JSON 后，前端如何使用

`api.ts`：

```typescript
return response.json();
```

`App.tsx`：

```typescript
const response = await analyzeFiles(files, question.trim());
setResult(response);
```

然后页面读：

```typescript
result.answer_text
result.parsed_files
result.retrieved_regulations
```

---

## 12. 当前 mock LLM 是怎么工作的

### 12.1 什么是 mock response

mock response 是“假的、固定的、用于演示和测试的响应”。

它不是模型真实生成的，但它的结构和真实结果相似。

当前 mock 在：

```text
backend/app/services/llm_client.py
```

函数：

```python
def _mock_response(self, prompt: str) -> str:
```

### 12.2 为什么没有 `LLM_API_KEY` 时要返回 mock

因为 demo 应该能在没有模型 key 的情况下跑通。

否则你第一次启动项目时，可能立刻遇到：

1. 没有 API key。
2. 模型服务不可用。
3. 网络不通。
4. 请求超时。
5. 模型返回格式不同。

这些会让你还没理解前后端，就被外部服务卡住。

### 12.3 mock response 对 demo 有什么好处

好处：

1. 不依赖千问3 API key。
2. 不依赖外部网络。
3. 保证前端展示逻辑可验证。
4. 保证后端接口可验证。
5. 保证文件上传和解析链路可验证。
6. 让开发重点先放在系统结构上。

### 12.4 什么时候会调用真实 LLM

当配置了：

```env
LLM_API_KEY=某个真实 key
```

并且 `LLM_BASE_URL` 指向真实 OpenAI-compatible 服务时，会调用真实 LLM。

代码判断：

```python
if not self.settings.llm_api_key:
    return self._mock_response(prompt)
```

只要 `llm_api_key` 非空，就会走真实调用。

### 12.5 `.env` 里配置什么后会调用真实 LLM

在 `backend/` 下创建 `.env`：

```bash
cp .env.example .env
```

然后填：

```env
LLM_BASE_URL=http://your-qwen-api-server/v1
LLM_API_KEY=你的真实 API key
LLM_MODEL=qwen3
```

注意：不要提交 `.env` 到 git。

### 12.6 OpenAI-compatible `/chat/completions` 是什么概念

OpenAI-compatible 的意思是：虽然服务可能不是 OpenAI 官方，但它模仿 OpenAI 的接口格式。

当前代码调用：

```text
{LLM_BASE_URL}/chat/completions
```

发送 payload：

```json
{
  "model": "qwen3",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.2
}
```

读取返回：

```python
data["choices"][0]["message"]["content"]
```

这就是典型的 chat completions 格式。

### 12.7 为什么没有千问3 API key 也能跑通

因为 `LLMClient.chat_completion()` 里先判断 API key：

```python
if not self.settings.llm_api_key:
    return self._mock_response(prompt)
```

所以没有 key 时：

1. 不会发送外部 HTTP 请求。
2. 不会报认证错误。
3. 直接返回 mock 文本。
4. 前端仍能展示结果。

---

## 13. 当前还没做的功能

下面这些不是漏做，而是故意留到后续 slice。

### 13.1 PDF 解析

当前 `document_parser.py` 不支持 PDF。

原因：

1. PDF 解析库需要额外依赖。
2. PDF 文本提取质量不稳定。
3. 扫描件还涉及 OCR。
4. 这会扩大 M0 范围。

### 13.2 docx 解析

当前不支持 docx。

原因：

1. 需要 `python-docx` 等依赖。
2. 表格、页眉页脚、批注等结构需要考虑。
3. 应该放到文档解析增强 slice。

### 13.3 xlsx 解析

当前不支持 xlsx。

原因：

1. 需要 `openpyxl` 等依赖。
2. Excel 有多个 sheet。
3. 单元格格式、公式、空行都需要处理策略。

### 13.4 ChromaDB

当前没有 ChromaDB。

原因：

1. M0 只验证上传和 mock 分析链路。
2. ChromaDB 涉及索引路径、collection、持久化、查询。
3. 需要先有制度 chunk。

### 13.5 embedding

当前没有 embedding。

原因：

1. embedding 需要模型或 API。
2. 需要处理批量文本。
3. 需要和 ChromaDB 写入流程配合。

### 13.6 制度文档向量化

当前没有制度文档向量化。

原因：

1. 需要制度文件解析。
2. 需要 chunk 切分策略。
3. 需要 embedding。
4. 需要向量数据库。

### 13.7 vector retrieval

当前没有真实向量检索。

虽然有 `vector_retriever.py`，但它返回：

```python
return []
```

这是占位，不是完整实现。

### 13.8 真实制度 RAG

当前没有真实制度 RAG。

RAG 至少需要：

1. 检索制度片段。
2. 把片段放进 prompt。
3. 要求模型基于片段回答。
4. 前端展示引用依据。

当前只保留了返回字段 `retrieved_regulations`。

### 13.9 案例库

当前没有案例库。

原因：

1. 案例库需要数据结构。
2. 需要检索策略。
3. 需要与制度 RAG 区分。

### 13.10 报告导出

当前没有报告导出。

原因：

1. 需要设计报告格式。
2. 需要 PDF/Word 生成。
3. 需要保存分析记录。

### 13.11 登录权限

当前没有登录权限。

原因：

1. 会引入用户体系。
2. 会引入权限边界。
3. 可能需要数据库。
4. 对 M0 闭环不是必需。

### 13.12 数据库

当前没有数据库。

原因：

1. M0 不需要保存业务记录。
2. 上传文件只是本地保存。
3. 分析结果直接返回前端。

---

## 14. 后续开发路线：每次只推进一个 slice

后续开发最重要的原则是：每次只推进一个切片，不要一口气做完整系统。

### Slice 1：文档解析增强

#### 目标

```text
支持 PDF / docx / xlsx 解析
```

#### 允许修改的文件

```text
backend/requirements.txt
backend/app/services/document_parser.py
docs/
```

#### 禁止修改的内容

```text
ChromaDB
embedding
RAG
前端大改
```

#### 验收标准

```text
上传 PDF/docx/xlsx 后能看到 parsed_files preview
```

更具体：

1. 上传 `.pdf` 返回 `status=parsed` 或清晰错误。
2. 上传 `.docx` 返回 `status=parsed` 或清晰错误。
3. 上传 `.xlsx` 返回 `status=parsed` 或清晰错误。
4. 不影响 `.txt`、`.md`、`.csv`。
5. 不影响 mock LLM。

#### 回滚建议

如果解析增强失败：

```bash
git diff
git checkout -- backend/requirements.txt backend/app/services/document_parser.py
```

如果已经提交：

```bash
git log --oneline
git revert <commit_sha>
```

#### commit message 建议

```bash
git commit -m "feat(parser): support pdf docx xlsx previews"
```

### Slice 2：制度文档 chunk 预处理

#### 目标

```text
扫描 data/regulations/raw/
解析制度文件
切成 chunks
返回 chunk 数量
```

#### 允许修改的文件

```text
backend/app/services/regulation_indexer.py
backend/app/main.py
backend/app/schemas.py
docs/
```

#### 禁止修改的内容

```text
embedding
ChromaDB
真实 RAG
LLM prompt 大改
前端大改
```

#### 验收标准

1. 可以扫描 `data/regulations/raw/`。
2. 可以把制度文本切成 chunks。
3. 可以返回 chunk 数量。
4. 不调用 embedding。
5. 不写 ChromaDB。

#### 回滚建议

```bash
git diff
git checkout -- backend/app/services/regulation_indexer.py backend/app/main.py backend/app/schemas.py docs/
```

如果已提交：

```bash
git revert <commit_sha>
```

#### commit message 建议

```bash
git commit -m "feat(indexer): add regulation chunk preprocessing"
```

### Slice 3：embedding + ChromaDB

#### 目标

```text
把制度 chunks 写入 ChromaDB
```

#### 允许修改的文件

```text
backend/requirements.txt
backend/app/services/embedding_client.py
backend/app/services/regulation_indexer.py
```

#### 禁止修改的内容

```text
前端展示
真实审计 RAG prompt 大改
登录权限
数据库
报告导出
```

#### 验收标准

1. embedding client 能把文本转向量。
2. regulation indexer 能把 chunks 写入 ChromaDB。
3. ChromaDB 数据写到预期目录。
4. 不改变 `/api/analyze` 的返回契约。

#### 回滚建议

```bash
git diff
git checkout -- backend/requirements.txt backend/app/services/embedding_client.py backend/app/services/regulation_indexer.py
```

如果已提交：

```bash
git revert <commit_sha>
```

#### commit message 建议

```bash
git commit -m "feat(vector): persist regulation embeddings to chromadb"
```

### Slice 4：vector_retriever

#### 目标

```text
根据 query 检索制度片段
```

#### 允许修改的文件

```text
backend/app/services/vector_retriever.py
backend/app/services/audit_engine.py
```

#### 禁止修改的内容

```text
文档解析增强
ChromaDB 写入逻辑大改
前端大改
登录权限
数据库
```

#### 验收标准

1. `vector_retriever.retrieve(query)` 返回 `RegulationChunk` 列表。
2. `audit_engine.analyze()` 能把检索片段放进 response。
3. 没有检索结果时仍返回空数组。
4. mock LLM 仍然可用。

#### 回滚建议

```bash
git diff
git checkout -- backend/app/services/vector_retriever.py backend/app/services/audit_engine.py
```

如果已提交：

```bash
git revert <commit_sha>
```

#### commit message 建议

```bash
git commit -m "feat(retriever): retrieve regulation chunks for audit queries"
```

### Slice 5：前端展示制度依据

#### 目标

```text
展示 retrieved_regulations
```

#### 允许修改的文件

```text
frontend/src/App.tsx
frontend/src/api.ts
frontend/src/App.css
```

#### 禁止修改的内容

```text
后端检索逻辑
ChromaDB
embedding
登录权限
报告导出
```

#### 验收标准

1. 前端能展示制度来源文件。
2. 前端能展示制度片段内容。
3. 前端能展示 score。
4. 空数组时仍显示空状态。
5. 不破坏文件解析状态展示。

#### 回滚建议

```bash
git diff
git checkout -- frontend/src/App.tsx frontend/src/api.ts frontend/src/App.css
```

如果已提交：

```bash
git revert <commit_sha>
```

#### commit message 建议

```bash
git commit -m "feat(frontend): show retrieved regulation references"
```

---

## 15. 我如何 review AI 生成的代码

这部分是你的“人工掌控清单”。每次 Codex 改完代码，你都按这个顺序查。

### 15.1 看当前状态

```bash
git status
```

你要看：

1. 哪些文件被修改。
2. 哪些文件是新增。
3. 有没有不该出现的文件。
4. 有没有 `.env`、上传文件、缓存文件。

### 15.2 看具体差异

```bash
git diff
```

重点看：

1. 有没有改功能代码。
2. 有没有改 API 字段名。
3. 有没有新增依赖。
4. 有没有把 mock 逻辑删掉。
5. 有没有引入数据库或 ChromaDB。

### 15.3 确认它没有改不该改的文件

例如 Slice 1 只允许改：

```text
backend/requirements.txt
backend/app/services/document_parser.py
docs/
```

你就看：

```bash
git status
```

如果出现：

```text
frontend/src/App.tsx
backend/app/services/audit_engine.py
```

就要问：为什么改了这些？

### 15.4 确认它没有偷偷加依赖

后端看：

```bash
git diff backend/requirements.txt
```

前端看：

```bash
git diff frontend/package.json
git diff frontend/package-lock.json
```

如果当前 slice 不允许加依赖，就不要接受。

### 15.5 确认 API 契约没有变

看：

```bash
git diff backend/app/schemas.py
git diff frontend/src/api.ts
git diff docs/api_contract.md
```

重点确认：

1. `answer_text` 还在。
2. `parsed_files` 还在。
3. `retrieved_regulations` 还在。
4. `filename/status/preview/error` 没乱改。

### 15.6 确认前端还能启动

```bash
cd /home/spark/workspace/audit-compliance-demo/frontend
npm run dev
```

如果只想验证构建：

```bash
npm run build
```

### 15.7 确认后端还能启动

```bash
cd /home/spark/workspace/audit-compliance-demo/backend
source .venv/bin/activate
fastapi dev app/main.py
```

然后测：

```bash
curl http://127.0.0.1:8000/health
```

### 15.8 确认 mock 模式还能跑

不要配置 `LLM_API_KEY`，然后请求：

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -F "question=请对这份材料做初步审计分析" \
  -F "files=@/path/to/example.txt"
```

确认返回里有：

```json
{
  "answer_text": "...",
  "parsed_files": [...],
  "retrieved_regulations": []
}
```

### 15.9 确认没有引入数据库或 ChromaDB

查依赖：

```bash
git diff backend/requirements.txt
```

查代码：

```bash
grep -R "chroma\|chromadb\|sqlite\|postgres\|mysql" -n backend frontend
```

如果当前 slice 不允许，就不要接受。

### 15.10 确认没有把 API key 写进代码

查：

```bash
grep -R "sk-\|api_key\|LLM_API_KEY" -n .
```

你要允许看到：

```text
backend/.env.example
backend/app/config.py
```

但不应该看到真实 key。

真实 key 只能放在 `.env`，并且 `.env` 不提交。

### 15.11 如何打 commit

确认没问题后：

```bash
git status
git diff
git add .
git commit -m "feat: describe your change"
```

例如当前文档可以是：

```bash
git commit -m "docs: add M0 project learning guide"
```

### 15.12 如何打 tag

当某个里程碑稳定后：

```bash
git tag m0-demo
```

查看 tag：

```bash
git tag
```

推送 tag：

```bash
git push origin m0-demo
```

### 15.13 如何回滚

如果还没 commit，只是工作区修改：

```bash
git status
git diff
git reset --hard
```

注意：`git reset --hard` 会丢弃所有未提交修改。使用前一定确认没有你想保留的内容。

如果已经 commit，建议用 revert：

```bash
git log --oneline
git revert <commit_sha>
```

如果要回到某个 tag：

```bash
git checkout m0-demo
```

如果你要在 tag 基础上新建分支：

```bash
git checkout -b recover-from-m0 m0-demo
```

---

## 16. 当前项目的最小掌控地图

你需要理解的核心链路只有这一条：

```text
frontend/src/App.tsx
  ↓ 调用
frontend/src/api.ts
  ↓ HTTP POST
backend/app/main.py
  ↓ 保存文件 + 调用
backend/app/services/document_parser.py
  ↓ 返回 parsed_files
backend/app/services/audit_engine.py
  ↓ 调用
backend/app/services/llm_client.py
  ↓ 返回 answer_text
backend/app/main.py
  ↓ 返回 JSON
frontend/src/App.tsx
  ↓ 展示结果
```

如果你只想掌控 M0 项目，优先读这 7 个文件：

```text
frontend/src/App.tsx
frontend/src/api.ts
backend/app/main.py
backend/app/schemas.py
backend/app/services/document_parser.py
backend/app/services/audit_engine.py
backend/app/services/llm_client.py
```

### 16.1 为什么 `frontend/src/App.tsx` 最重要

因为它是用户看到的主页面。

你能在这里理解：

1. 用户怎么选择文件。
2. 用户怎么输入问题。
3. 用户怎么点击按钮。
4. 前端怎么保存 loading/error/result。
5. 前端怎么展示后端结果。

### 16.2 为什么 `frontend/src/api.ts` 最重要

因为它是前端和后端之间的桥。

你能在这里理解：

1. 文件如何放进 `FormData`。
2. 前端如何调用 `/api/analyze`。
3. 后端错误如何变成前端错误。
4. TypeScript 类型如何对齐后端 schema。

### 16.3 为什么 `backend/app/main.py` 最重要

因为它是后端 API 入口。

你能在这里理解：

1. `/health` 怎么定义。
2. `/api/analyze` 怎么定义。
3. FastAPI 如何接收文件和表单字段。
4. 文件如何保存。
5. 后端如何调用 parser 和 engine。

### 16.4 为什么 `backend/app/schemas.py` 最重要

因为它定义 API 数据契约。

你能在这里理解：

1. 后端返回什么字段。
2. 每个字段是什么类型。
3. 前端为什么能读 `answer_text` 和 `parsed_files`。
4. 未来 `retrieved_regulations` 如何扩展。

### 16.5 为什么 `backend/app/services/document_parser.py` 最重要

因为它是文件内容进入系统的第一层处理。

你能在这里理解：

1. 当前支持哪些文件。
2. 不支持文件如何处理。
3. 文件解析失败为什么不会拖垮整个请求。
4. preview 是如何生成的。

### 16.6 为什么 `backend/app/services/audit_engine.py` 最重要

因为它是业务编排中心。

你能在这里理解：

1. prompt 如何拼接。
2. 解析结果如何进入模型上下文。
3. 为什么当前制度检索为空。
4. 未来 RAG 应该接在哪里。

### 16.7 为什么 `backend/app/services/llm_client.py` 最重要

因为它决定系统是否调用真实模型。

你能在这里理解：

1. 没有 key 为什么返回 mock。
2. 有 key 时如何调用 `/chat/completions`。
3. LLM 返回内容如何变成 `answer_text`。

---

## 17. 当前实现与预期差异

这一节专门记录“文档描述或用户心中的概念”和“当前代码实际实现”之间的小差异。这里只解释，不改代码。

### 17.1 前端没有单独的 `answerText / parsedFiles / retrievedRegulations` state

用户在学习状态管理时提到：

```typescript
answerText
parsedFiles
retrievedRegulations
```

当前代码实际是：

```typescript
const [result, setResult] = useState<AnalyzeResponse | null>(null);
```

然后通过：

```typescript
result.answer_text
result.parsed_files
result.retrieved_regulations
```

来展示。

这不是错误。M0 项目里统一用 `result` 更简单。

### 17.2 当前 `api.ts` 没有 `API_BASE_URL`

用户要求解释 `API_BASE_URL`。

当前代码实际没有定义：

```typescript
const API_BASE_URL = ...
```

而是使用：

```typescript
fetch("/api/analyze")
```

并通过 Vite proxy 转发到后端。

这也是合理实现。

### 17.3 当前 parser 方法名是 `parse()`，不是 `parse_file()`

用户流程图里写了：

```text
document_parser.parse_file()
```

当前实际代码是：

```python
parser.parse(saved_path, safe_name)
```

方法名不同，但职责一致。

### 17.4 当前项目里存在运行验证产生的目录

当前工作区可能存在：

```text
backend/.venv/
frontend/node_modules/
frontend/dist/
backend/app/__pycache__/
```

这些是安装依赖、构建或运行验证产生的，不是业务代码。

`.gitignore` 已经忽略了主要运行产物。你阅读项目时可以先忽略它们。

---

## 18. 建议阅读顺序

如果你现在感觉信息很多，不要从头到尾硬背。按这个顺序读代码：

### 第一步：先看前端入口

```text
frontend/src/App.tsx
```

只看三件事：

1. state。
2. `handleFileChange()`。
3. `handleSubmit()`。

### 第二步：看前端 API

```text
frontend/src/api.ts
```

只看：

1. `FormData`。
2. `fetch("/api/analyze")`。
3. `AnalyzeResponse` type。

### 第三步：看后端入口

```text
backend/app/main.py
```

只看：

1. `/health`。
2. `/api/analyze`。
3. 保存上传文件。
4. 调用 parser 和 engine。

### 第四步：看数据结构

```text
backend/app/schemas.py
```

把它和 `frontend/src/api.ts` 对照起来看。

### 第五步：看解析

```text
backend/app/services/document_parser.py
```

理解 `parsed / unsupported / failed`。

### 第六步：看业务编排

```text
backend/app/services/audit_engine.py
```

理解 prompt 是怎么拼出来的。

### 第七步：看模型调用

```text
backend/app/services/llm_client.py
```

理解 mock 和真实 LLM 的分支。

---

## 19. 最后给你的掌控感总结

你现在不需要理解 ChromaDB。

你现在也不需要理解 embedding。

你甚至不需要急着理解完整 RAG。

当前 M0 你只要能讲清楚这句话，就已经掌控了项目核心：

```text
前端 App.tsx 让用户选择文件和输入问题，
api.ts 用 FormData 调用后端 /api/analyze，
main.py 接收并保存文件，
document_parser.py 解析 txt/md/csv，
audit_engine.py 拼 prompt，
llm_client.py 没有 API key 就返回 mock，
FastAPI 把 AnalyzeResponse 转成 JSON，
App.tsx 再把 answer_text 和 parsed_files 展示出来。
```

后续每加一个功能，都应该问：

1. 它属于哪个 slice？
2. 它应该改哪个文件？
3. 它是否改变 API 契约？
4. 它是否引入新依赖？
5. 它是否破坏 mock 模式？
6. 它是否让你更掌控，而不是更混乱？

只要你坚持按 slice 推进，这个项目会一直保持可理解、可回滚、可扩展。
