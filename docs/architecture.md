# AuditPilot 审计合规智能分析 Demo
# 需求、架构、TDD 与技术选型总控文档 v1.0

> 项目名：AuditPilot / audit-compliance-demo  
> 当前阶段：M0+ → 文档解析增强与 OCR 接入阶段  
> 文档用途：给个人助手 agent / Hermes / Claude / Codex 作为监督 Codex 执行的单一真相源  
> 核心原则：小步推进、测试先行、架构不越界、每个功能必须有可验证测试  
> LLM 友好说明：本文档使用稳定标题、明确约束、允许/禁止清单、测试清单和执行模板，便于 agent 逐段读取与执行。

---

## 0. 文档目标与使用方式

本文档合并了两类内容：

1. **需求、架构与 TDD 监督规则**  
   用来约束 Codex 不要越界开发，确保每个功能都测试先行、可回滚、可验收。

2. **技术栈选型与实现细节**  
   用来明确 OCR、文档解析、本地 Qwen、embedding、向量数据库、RAG、部署等技术路线。

本文档不是要求 Codex 立刻实现所有功能。它的作用是：

- 明确当前要做什么、不做什么。
- 明确后续技术组件应该怎么选。
- 明确每个 Slice 的允许修改范围。
- 明确每个 Slice 必须先写哪些测试。
- 明确个人助手 agent 如何监督 Codex。
- 明确用户如何通过测试、diff、commit、tag 重新获得项目掌控感。

---

## 1. 项目背景

审计部门希望有一个 AI 辅助分析 demo。

业务场景是：

用户上传审计材料，例如：

- 招投标材料
- 采购材料
- 合同材料
- 审批材料
- 扫描版文件
- 图片版文档
- Word / Excel / PDF 文件

系统需要读取材料内容，并调用大模型生成初步审核意见。

当前 manager 已明确：

1. 审计案例数据不能出院，暂时无法提供。
2. 先把基础功能调通。
3. 文档扫描图片很多，需要考虑图片文字提取。
4. 系统需要部署在院内机器上。
5. 暂时不追求准确率。
6. 当前重点是材料读取能力，而不是案例库。

因此，当前阶段的关键任务不是案例库，也不是完整 RAG，而是：

```text
上传材料
→ 解析文本
→ OCR 提取扫描图片文字
→ 调用本地 Qwen 或 mock LLM
→ 输出 AI 初步辅助审核意见
→ 前端展示
```

---

## 2. 产品定位

AuditPilot 当前版本定位为：

> 审计材料 AI 初步风险筛查 demo。

它不是：

- 最终审计判定系统
- 法律结论生成系统
- 完整知识库平台
- 完整 RAG 系统
- 审计案例管理系统
- 自动审批系统
- 自主 agent 系统

它当前只做：

> 帮审计人员快速把上传材料转成可读文本，并让大模型基于这些文本生成初步风险提示。

所有输出都必须包含人工复核提示。

系统输出不得声称：

```text
该材料最终合规。
该材料最终不合规。
系统已完成审计。
```

只能说：

```text
AI 初步判断……
可能存在……
需要人工复核……
当前材料证据不足……
OCR 识别可能存在误差……
制度有效性需要人工确认……
```

---

## 3. 当前 M0 已完成内容

当前 M0 骨架已完成：

1. React + Vite + TypeScript 前端。
2. FastAPI 后端。
3. `GET /health`。
4. `POST /api/analyze`。
5. 多文件上传。
6. 上传文件保存到 `backend/uploads/`。
7. `.txt` / `.md` / `.csv` 基础解析。
8. 不支持格式返回 `unsupported`。
9. `audit_engine.py` 作为业务编排入口。
10. `llm_client.py` 支持 mock response。
11. 没有 `LLM_API_KEY` 时系统也能跑通。
12. 前端展示：
    - `answer_text`
    - `parsed_files`
    - `retrieved_regulations` 空状态
13. 预留模块：
    - `regulation_indexer.py`
    - `embedding_client.py`
    - `vector_retriever.py`

当前 M0 的核心链路是：

```text
frontend/src/App.tsx
  ↓
frontend/src/api.ts
  ↓
backend/app/main.py
  ↓
backend/app/services/document_parser.py
  ↓
backend/app/services/audit_engine.py
  ↓
backend/app/services/llm_client.py
  ↓
backend/app/schemas.py
  ↓
frontend/src/App.tsx
```

---

## 4. 当前最重要的新需求：OCR

manager 最新需求指出：

> 图片也是文档扫描的，可不可以前边加个处理图片的工具，提取图片里面的文字。

因此，当前优先级调整为：

```text
第一优先级：图片 OCR 和扫描件解析
第二优先级：PDF / Word / Excel 解析
第三优先级：部署在院内机器
第四优先级：制度文档向量化
第五优先级：RAG 检索
第六优先级：案例库
```

OCR 是当前阶段的关键功能，因为：

1. 如果图片文字提取不出来，后续 LLM 无法分析。
2. 如果扫描 PDF 无法解析，审计材料会大量失败。
3. 案例暂时不能提供，系统价值主要来自“材料解析 + AI 初步分析”。
4. 部署在院内机器意味着 OCR 方案应优先考虑本地执行，避免材料外传。

---

## 5. 总体架构

当前架构采用普通 FastAPI 文档分析 pipeline，不采用自主 agent 后端。

整体流程：

```text
用户浏览器
  ↓
React 前端
  ↓
POST /api/analyze
  ↓
FastAPI 后端 main.py
  ↓
保存上传文件
  ↓
document_parser.py
  ├── 文本文件解析
  ├── PDF 解析
  ├── Word 解析
  ├── Excel 解析
  └── OCR 图片文字提取
  ↓
audit_engine.py
  ↓
llm_client.py
  ↓
AnalyzeResponse JSON
  ↓
React 前端展示
```

未来加入制度 RAG 后，流程会变成：

```text
上传材料
  ↓
document_parser.py 解析材料
  ↓
vector_retriever.py 检索制度片段
  ↓
audit_engine.py 拼接材料 + 制度片段 + prompt
  ↓
llm_client.py 调用模型
  ↓
前端展示 AI 初步意见 + 制度引用
```

---

## 6. 架构不变量

以下规则不允许被 Codex 修改。

### 6.1 `audit_engine.py` 是唯一业务编排者

`audit_engine.py` 负责：

1. 接收用户问题。
2. 接收解析后的文件。
3. 后续接收制度检索片段。
4. 拼接 prompt。
5. 调用 `llm_client.py`。
6. 组装响应结果。

其他模块不允许包含审计业务编排逻辑。

禁止：

```text
document_parser.py 里写审计判断逻辑
llm_client.py 里写审计 prompt
vector_retriever.py 里调用 LLM
main.py 里塞大量业务逻辑
```

### 6.2 `llm_client.py` 只负责模型传输

`llm_client.py` 只做：

```text
messages / prompt
  ↓
OpenAI-compatible API
  ↓
response text
```

它不负责：

- 审计判断
- prompt 设计
- 文件解析
- 制度检索
- OCR
- 风险等级规则

后续从 Qwen3 切换到 DeepSeek 时，只允许改 `llm_client.py` 或配置，不应该改业务流程。

### 6.3 `document_parser.py` 只负责文件转文本

`document_parser.py` 负责把上传文件变成文本。

允许它调用：

- `ocr_service.py`
- PDF 解析库
- Word 解析库
- Excel 解析库

不允许它：

- 调用 LLM
- 检索制度
- 判断合规
- 输出审计结论

### 6.4 `ocr_service.py` 只负责 OCR

新增 `ocr_service.py` 后，它只负责：

```text
图片路径
  ↓
OCR
  ↓
文字
```

它不负责：

- 文件上传
- 审计判断
- LLM 调用
- RAG 检索
- prompt 拼接

### 6.5 `schemas.py` 是 API 数据契约中心

所有 API 返回结构必须通过 `schemas.py` 维护。

不允许前端和后端私自约定隐形字段。

如果修改返回结构，必须：

1. 修改 `schemas.py`。
2. 修改前端 TypeScript 类型。
3. 修改 API 文档。
4. 增加或更新测试。

### 6.6 当前阶段不引入数据库

当前阶段不做：

- 用户系统
- 权限系统
- 审计记录持久化
- 任务队列
- 审计历史管理

上传文件可以保存在本地 `backend/uploads/`。

### 6.7 当前阶段不实现案例库

因为审计案例不能出院，暂时不给。

不允许 Codex 主动实现：

- case database
- case retriever
- few-shot case store
- case upload UI
- case management API

案例库留到后续需求明确后再设计。

---

## 7. 当前推荐项目目录

当前项目目录应保持如下方向：

```text
audit-compliance-demo/
  frontend/
    src/
      App.tsx
      api.ts
      main.tsx
      App.css

  backend/
    app/
      main.py
      config.py
      schemas.py

      services/
        document_parser.py
        ocr_service.py
        audit_engine.py
        llm_client.py
        regulation_indexer.py
        embedding_client.py
        vector_retriever.py

      prompts/
        audit_prompt.txt

    uploads/
    requirements.txt
    .env.example

  data/
    regulations/
      raw/
    indexes/
      chroma/
        regulations/
    samples/

  docs/
    requirements_architecture_tdd_technical_v1.md
    project_learning_guide.md
    architecture_v2_demo_vector.md
    api_contract.md
    demo_script.md

  README.md
```

说明：

1. `ocr_service.py` 是下一阶段新增模块。
2. `regulation_indexer.py`、`embedding_client.py`、`vector_retriever.py` 当前仍然是未来预留模块。
3. 当前阶段不允许实现完整 ChromaDB。
4. 当前阶段不允许实现案例库。

---

## 8. 当前 API 契约

### 8.1 健康检查

```http
GET /health
```

返回：

```json
{
  "status": "ok"
}
```

测试要求：

```bash
curl http://127.0.0.1:8000/health
```

必须返回 `{"status":"ok"}`。

### 8.2 上传并分析

```http
POST /api/analyze
```

请求类型：

```text
multipart/form-data
```

字段：

```text
files: File[]
question: string
```

返回：

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

当前阶段 `retrieved_regulations` 可以为空。

未来接入制度检索后，该字段填充制度片段。

---

## 9. 文件解析需求

### 9.1 当前已支持

```text
.txt
.md
.csv
```

状态：

```text
parsed
unsupported
failed
```

### 9.2 下一阶段必须支持：图片 OCR

目标支持：

```text
.jpg
.jpeg
.png
.bmp
.tiff
.webp
```

要求：

1. 上传图片后，系统使用本地 OCR 提取文字。
2. OCR 成功时返回 `status="ocr_parsed"`。
3. OCR 识别不到文字时返回 `status="failed"`。
4. OCR 出错不能导致整个 `/api/analyze` 请求失败。
5. 多文件上传时，一个图片失败不影响其他文件。
6. OCR 文本进入 `preview`。
7. OCR 文本应进入后续 `audit_engine` prompt。
8. 前端能展示 OCR 解析状态。

### 9.3 后续支持：扫描版 PDF

扫描版 PDF 处理流程：

```text
PDF
  ↓
检测是否可直接抽文本
  ↓
如果有文本：直接用 PDF text extraction
  ↓
如果几乎没有文本：将页面渲染成图片
  ↓
调用 OCR
  ↓
合并每页 OCR 文本
```

扫描版 PDF 可以在 OCR 图片支持稳定后再做。

### 9.4 后续支持：PDF / docx / xlsx

目标支持：

```text
.pdf
.docx
.xlsx
```

推荐库：

```text
PDF: PyMuPDF
Word: python-docx
Excel: openpyxl
```

注意：

1. PDF 可能是文本型，也可能是扫描型。
2. Word 可能有表格。
3. Excel 可能有多个 sheet。
4. 解析失败必须 graceful fallback。

---

## 10. 技术栈总览

### 10.1 当前 M0+ 推荐技术栈

| 层级 | 当前推荐 | 说明 |
|---|---|---|
| 前端 | React + Vite + TypeScript | 已搭好，保持不变 |
| 后端 | FastAPI + Python | 已搭好，保持不变 |
| 文本文件解析 | Python 原生读取 | 支持 txt/md/csv |
| PDF 解析 | PyMuPDF | 适合文本型 PDF 和页面渲染 |
| Word 解析 | python-docx | 解析 docx 段落和表格 |
| Excel 解析 | openpyxl | 解析 xlsx sheet |
| 图片 OCR | PaddleOCR | 优先本地 OCR，适合中文扫描件 |
| OCR fallback | Tesseract，可选 | PaddleOCR 不可用时的备选 |
| LLM | 本地 Qwen 文本模型 | 通过 OpenAI-compatible API 接入 |
| LLM 服务框架 | vLLM / SGLang / Ollama / LMDeploy 视现有环境而定 | 不在业务代码中绑定具体框架 |
| Embedding | BGE-M3 或 bge-small-zh | 后续 RAG 阶段使用 |
| 向量数据库 | ChromaDB local persistent | demo 阶段最轻量 |
| 测试 | pytest + FastAPI TestClient | 后端 TDD |
| 前端测试 | Vitest + Testing Library，后续引入 | 当前可先 npm build |

---

## 11. 本地 Qwen 文本模型接入

用户当前已经有本地文本版 Qwen 模型。

### 11.1 本地 Qwen 在系统里的角色

本地 Qwen 当前应该作为：

```text
LLM 生成模型
```

它负责：

1. 阅读上传材料文本。
2. 阅读 OCR 提取文本。
3. 阅读后续检索到的制度片段。
4. 输出 AI 初步审核意见。

它不应该默认作为：

```text
embedding 模型
```

除非当前本地 Qwen 服务明确提供 embedding endpoint。

换句话说：

> 本地 Qwen 文本模型负责“写答案”，embedding 模型负责“把文本变成向量”。这两个角色不要混淆。

### 11.2 本地 Qwen 推荐接入方式

后端 `llm_client.py` 不应该直接依赖某个具体部署框架。

推荐统一抽象为：

```text
OpenAI-compatible /chat/completions
```

环境变量：

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=http://127.0.0.1:8000/v1
LLM_API_KEY=EMPTY_OR_LOCAL_KEY
LLM_MODEL=qwen-local
```

业务代码只知道：

```text
我要向 LLM_BASE_URL/chat/completions 发请求
```

它不关心背后是：

1. vLLM
2. SGLang
3. Ollama
4. LMDeploy
5. 其他院内模型服务
6. 远程 Qwen API
7. 未来 DeepSeek

### 11.3 本地 Qwen 接入原则

`llm_client.py` 必须满足：

1. 无 API key 时仍能 mock fallback。
2. 有本地 endpoint 时调用本地 Qwen。
3. 不在代码里写死模型名。
4. 不在代码里写死 IP 地址。
5. 不在代码里写死 API key。
6. temperature 默认低一些，例如 0 或 0.1。
7. timeout 要可配置。
8. 模型失败时返回清晰错误，不让后端崩掉。

推荐配置：

```env
LLM_BASE_URL=http://127.0.0.1:8000/v1
LLM_API_KEY=local-dummy-key
LLM_MODEL=qwen-local
LLM_TEMPERATURE=0.1
LLM_TIMEOUT_SECONDS=120
```

### 11.4 本地 Qwen 测试策略

必须有测试：

1. 没有 `LLM_API_KEY` 时返回 mock。
2. 有 `LLM_API_KEY` 时调用 HTTP endpoint。
3. endpoint 超时有清晰错误。
4. endpoint 返回格式异常时有 graceful error。
5. `llm_client.py` 不包含审计业务逻辑。

测试中不应该真的启动 Qwen。测试应该 mock HTTP 响应。

---

## 12. OCR 技术选型

### 12.1 OCR 的业务重要性

当前 manager 明确指出图片和扫描件很多。因此 OCR 不是锦上添花，而是审计材料解析的核心入口之一。

很多审计材料可能是：

1. 扫描 PDF。
2. 盖章页图片。
3. 手机拍照材料。
4. 图片版合同。
5. 图片版审批单。
6. 图片版发票或付款凭证。

如果 OCR 不做，这些材料对 LLM 来说就是“空白”。

### 12.2 OCR 首选：PaddleOCR

当前推荐首选：

```text
PaddleOCR
```

原因：

1. 对中文场景友好。
2. 适合扫描件、截图、图片版文档。
3. 可以本地部署。
4. 不需要把审计材料发到外部云端。
5. 生态较成熟。
6. 后续可以升级到结构化文档解析方案。

推荐当前先使用：

```text
PaddleOCR 普通 OCR pipeline
```

而不是一开始使用复杂文档理解模型。

### 12.3 PaddleOCR 在本项目中的定位

PaddleOCR 当前只作为：

```text
图片文字提取器
```

输入：

```text
图片路径
```

输出：

```text
OCR 文本
```

不要求它当前做：

1. 表格结构恢复。
2. 版面理解。
3. 印章真伪判断。
4. 手写签名识别。
5. 票据字段结构化抽取。
6. 多模态审计判断。

当前只需要：

> 把图片里的可见打印体文字尽量转成普通文本。

### 12.4 OCR 服务模块设计

新增：

```text
backend/app/services/ocr_service.py
```

推荐接口：

```python
class OCRService:
    def extract_text_from_image(self, image_path: Path) -> str:
        ...
```

`document_parser.py` 负责判断文件后缀：

```text
.jpg
.jpeg
.png
.bmp
.tiff
.webp
```

如果是图片，就调用：

```python
ocr_service.extract_text_from_image(path)
```

成功：

```text
status = "ocr_parsed"
```

失败：

```text
status = "failed"
```

### 12.5 OCR 不可用时的 fallback

因为 PaddleOCR 依赖比较重，所以必须考虑：

1. PaddleOCR 没安装。
2. 模型下载失败。
3. 院内机器无网。
4. CPU 推理过慢。
5. 图片质量太差。
6. OCR 抛异常。

所有这些情况都不能导致 `/api/analyze` 500。

正确行为：

```json
{
  "filename": "scan.png",
  "status": "failed",
  "preview": "",
  "error": "OCR backend unavailable or no text detected"
}
```

如果多文件上传，某个图片 OCR 失败，不影响其他文件继续解析。

### 12.6 OCR 测试策略

OCR 测试必须分两类。

#### A. Mock OCR 单元测试

这些测试不依赖真实 PaddleOCR。

测试点：

1. 图片后缀会触发 OCRService。
2. OCRService 返回文本时，`document_parser` 返回 `ocr_parsed`。
3. OCRService 返回空文本时，`document_parser` 返回 `failed`。
4. OCRService 抛异常时，`document_parser` 返回 `failed`。
5. OCR 失败不影响 txt 文件解析。

#### B. 手动 OCR 验收测试

使用真实图片：

```text
backend/tests/fixtures/sample_scan.png
```

手动验证：

1. 后端能启动。
2. 上传图片后能返回 OCR 文本。
3. 前端能展示 `ocr_parsed`。
4. 模糊图片会有合理失败提示。

真实 PaddleOCR 不建议作为基础 CI 测试依赖。

### 12.7 OCR 的已知限制

必须在文档和前端提示中说明：

OCR 不保证准确识别：

1. 手写字。
2. 模糊扫描件。
3. 严重倾斜图片。
4. 复杂表格结构。
5. 印章内容。
6. 签名真实性。
7. 被遮挡文字。
8. 低分辨率图片。

标准提示语：

```text
OCR 识别文本可能存在误差，扫描件、手写内容、盖章页和复杂表格需人工复核。
```

---

## 13. 文档解析技术选型

### 13.1 文本文件

支持：

```text
.txt
.md
.csv
```

实现方式：

1. txt/md：原生 `Path.read_text()`。
2. csv：Python csv 模块或直接文本读取。

测试：

1. UTF-8 文本。
2. 空文件。
3. 非 UTF-8 fallback。
4. csv 多行预览。
5. 大文件截断 preview。

### 13.2 PDF 解析

推荐：

```text
PyMuPDF
```

原因：

1. 中文 PDF 文本抽取通常比简单 PDF 库更稳定。
2. 支持按页读取。
3. 支持将页面渲染为图片，便于扫描 PDF OCR fallback。
4. 适合后续“文本型 PDF + 扫描 PDF”统一处理。

PDF 解析策略：

```text
先尝试直接抽取文本
如果文本量足够 → 返回 parsed
如果文本量很少 → 判断可能是扫描 PDF
后续 Slice 再触发 OCR fallback
```

当前分阶段：

1. Slice 1B：支持文本型 PDF。
2. Slice 1C：支持扫描 PDF OCR fallback。

### 13.3 Word 解析

推荐：

```text
python-docx
```

支持：

1. 段落文本。
2. 表格文本。
3. 基础标题结构。

不支持：

1. `.doc` 老格式。
2. 复杂嵌入对象。
3. 图片中的文字。
4. 批注和修订痕迹，除非后续专门处理。

测试：

1. 普通段落。
2. 多段落。
3. 表格。
4. 空文档。
5. 异常文件。

### 13.4 Excel 解析

推荐：

```text
openpyxl
```

支持：

1. `.xlsx`
2. 多 sheet
3. 单元格文本
4. markdown-like 表格输出

不支持：

1. `.xls`
2. 公式求值准确性保证
3. 图片内文字
4. 复杂样式
5. 宏

输出格式建议：

```text
[Sheet: Sheet1]
| A | B | C |
| 项目 | 金额 | 审批人 |
| ... |
```

测试：

1. 单 sheet。
2. 多 sheet。
3. 空 sheet。
4. 数字和日期。
5. 大表格截断。

---

## 14. Embedding 模型选型

### 14.1 Embedding 在项目中的角色

Embedding 用于后续 RAG。

它负责：

```text
把制度片段变成向量
把用户问题变成向量
通过向量相似度找相关制度片段
```

Embedding 不负责：

1. 生成答案。
2. 审计判断。
3. OCR。
4. 文档解析。
5. 案例推理。

### 14.2 本地 Qwen 文本模型不能默认当 embedding

用户本地已有 Qwen 文本模型。

但需要注意：

> Qwen 文本生成模型 ≠ embedding 模型。

如果当前本地 Qwen 服务只支持：

```text
/chat/completions
```

那它只能作为 LLM。

只有当它明确支持：

```text
/embeddings
```

或提供 embedding 模型 endpoint，才可以作为 embedding provider。

否则应该单独部署 embedding 模型。

### 14.3 当前推荐 embedding：BGE-M3

推荐优先级：

```text
第一选择：BAAI/bge-m3
第二选择：bge-small-zh / bge-large-zh
第三选择：院内已有 embedding 服务
第四选择：Qwen embedding API，如果院内已有
```

BGE-M3 推荐原因：

1. 支持多语言。
2. 适合中文和英文混合。
3. 支持 dense retrieval。
4. 后续可支持更复杂检索能力。
5. 适合法规、制度、长文档检索场景。
6. 本地可部署，避免材料出院。

### 14.4 轻量版本选择

如果院内机器资源有限，可以先用：

```text
bge-small-zh
```

优点：

1. 模型较小。
2. 推理更快。
3. 本地部署更轻。
4. demo 阶段够用。

缺点：

1. 长文档和复杂语义召回可能弱于 BGE-M3。
2. 后续正式系统可能需要升级。

### 14.5 Embedding 接口设计

`embedding_client.py` 推荐接口：

```python
class EmbeddingClient:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...
```

支持 provider：

```env
EMBEDDING_PROVIDER=local_bge
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu
```

或：

```env
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_BASE_URL=http://127.0.0.1:9000/v1
EMBEDDING_API_KEY=local-dummy-key
EMBEDDING_MODEL=bge-m3
```

业务代码不应该关心 embedding 背后是本地模型还是 HTTP 服务。

### 14.6 Embedding 测试策略

不允许基础测试真的下载大模型。

必须用 mock embedding：

```python
def fake_embed_texts(texts):
    return [[0.1, 0.2, 0.3] for _ in texts]
```

测试点：

1. 输入 N 条文本，返回 N 个向量。
2. 空文本列表返回空列表。
3. embedding 失败有清晰错误。
4. indexer 能消费 embedding client。
5. 不同 provider 不影响上层接口。

---

## 15. 向量数据库选型

### 15.1 当前推荐：ChromaDB local persistent

当前 demo 阶段推荐：

```text
ChromaDB
```

部署方式：

```text
local persistent mode
```

原因：

1. 不需要单独启动数据库服务。
2. Python 集成简单。
3. 适合 demo 和小规模制度库。
4. 支持本地持久化。
5. 支持 metadata。
6. 后续可以替换为 Qdrant / Milvus / pgvector。

推荐路径：

```text
data/indexes/chroma/regulations/
```

### 15.2 当前为什么不选 Milvus

Milvus 更适合：

1. 大规模向量数据。
2. 多用户服务。
3. 生产级向量检索。
4. 集群部署。

但对当前 demo 来说：

1. 部署重。
2. 运维成本高。
3. 开发认知负担大。
4. 不符合一周 demo 的目标。

所以当前不选。

### 15.3 当前为什么不选 Qdrant

Qdrant 很好，适合生产服务化部署。

但当前阶段：

1. 需要额外服务。
2. 需要管理端口。
3. 需要部署配置。
4. 对初学者增加复杂度。

因此后续如果正式化，可以考虑 Qdrant。M0+/M1 先用 ChromaDB。

### 15.4 当前为什么不选 pgvector

pgvector 适合已有 PostgreSQL 的系统。

但当前项目明确暂时不做数据库。

所以不引入 PostgreSQL，也不引入 pgvector。

### 15.5 ChromaDB 接口设计

推荐新增：

```text
backend/app/services/regulation_indexer.py
backend/app/services/vector_retriever.py
```

职责划分：

```text
regulation_indexer.py
  负责扫描制度文件、解析、chunk、embedding、写入 ChromaDB

vector_retriever.py
  负责根据 query 从 ChromaDB 读取 top_k chunks
```

不允许：

```text
audit_engine.py 直接操作 ChromaDB
main.py 直接操作 ChromaDB
llm_client.py 操作 ChromaDB
```

### 15.6 ChromaDB 测试策略

基础测试不要依赖真实 embedding。

测试分两层：

#### A. Indexer 单元测试

使用 fake embedding。

测试：

1. chunk 可以写入 mock collection。
2. 文件路径 metadata 保留。
3. chunk_id 唯一。
4. 空文档不会崩。
5. unsupported 文件会跳过或记录失败。

#### B. Retriever 集成测试

可以使用临时目录 ChromaDB。

测试：

1. 写入几个 fake chunk。
2. query 能返回 top_k。
3. 空库返回空列表。
4. score / metadata 返回结构正确。
5. retrieved chunk 能转成 `RegulationChunk` schema。

---

## 16. RAG 技术路线

### 16.1 当前不做正式 RAG

当前阶段优先：

```text
文档解析 + OCR + 本地 Qwen 分析
```

RAG 推迟到文档解析稳定之后。

原因：

1. 如果材料读不出来，RAG 没用。
2. 如果 OCR 失败，RAG 没用。
3. 当前案例不给，制度库也未治理。
4. 当前 manager 目标是先调通。

### 16.2 Demo 版 RAG 方案

后续如果进入 RAG，采用：

```text
全量制度文档向量化
不做制度版本治理
不做 active/archive
不做 manifest
```

流程：

```text
data/regulations/raw/
  ↓
document_parser 解析制度文件
  ↓
chunk 分割
  ↓
embedding_client
  ↓
ChromaDB
  ↓
vector_retriever
  ↓
audit_engine 拼入 prompt
```

注意：

因为不做制度治理，所以 prompt 必须提示：

```text
检索到的制度片段可能来自历史制度或修订前文件，最终制度有效性需要人工确认。
```

### 16.3 正式版 RAG 升级

当客户开始要求准确性后，再加入：

1. 制度版本治理。
2. active/archive/uncertain。
3. manifest.yaml。
4. metadata filter。
5. BM25 + vector hybrid。
6. reranker。
7. 案例库。
8. 人工审核闭环。

---

## 17. Chunk 切分策略

### 17.1 Demo 阶段

推荐简单策略：

```text
按段落合并
每个 chunk 800-1200 中文字符
chunk overlap 100-200 字
```

原因：

1. 实现简单。
2. 不依赖制度格式规整。
3. 适合混乱制度文件。
4. demo 足够。

### 17.2 后续正式阶段

正式阶段可以改为：

1. 按“第 X 条”切。
2. 按章节切。
3. 按表格单元切。
4. 按文档结构切。
5. OCR 文档按页切。

但当前不优先。

### 17.3 Chunk metadata

每个 chunk 至少保留：

```python
{
    "chunk_id": str,
    "source_file": str,
    "content": str,
    "page": int | None,
    "chunk_index": int,
    "year_hint": str | None
}
```

`year_hint` 可以从文件名正则提取，仅用于展示，不做有效性判断。

---

## 18. 配置设计

### 18.1 LLM 配置

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=http://127.0.0.1:8000/v1
LLM_API_KEY=local-dummy-key
LLM_MODEL=qwen-local
LLM_TEMPERATURE=0.1
LLM_TIMEOUT_SECONDS=120
```

### 18.2 OCR 配置

```env
OCR_PROVIDER=paddleocr
OCR_DEVICE=cpu
OCR_LANG=ch
OCR_ENABLE=true
OCR_MAX_IMAGE_SIZE_MB=20
OCR_TIMEOUT_SECONDS=120
```

如果 PaddleOCR 不可用：

```env
OCR_PROVIDER=disabled
```

此时图片返回：

```text
failed: OCR disabled
```

### 18.3 Embedding 配置

```env
EMBEDDING_PROVIDER=local_bge
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu
EMBEDDING_BATCH_SIZE=16
```

或：

```env
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_BASE_URL=http://127.0.0.1:9000/v1
EMBEDDING_API_KEY=local-dummy-key
EMBEDDING_MODEL=bge-m3
```

### 18.4 Chroma 配置

```env
CHROMA_PERSIST_DIR=../data/indexes/chroma/regulations
CHROMA_COLLECTION_NAME=regulations
```

---

## 19. 依赖分阶段加入

### 19.1 当前 M0 依赖

```text
fastapi[standard]
pydantic-settings
python-multipart
httpx
```

### 19.2 TDD 测试依赖

进入测试补齐时加入：

```text
pytest
pytest-asyncio
```

### 19.3 OCR Slice 依赖

进入图片 OCR 时再加入：

```text
paddleocr
pillow
```

如果 PaddleOCR 安装过重，可先通过可注入 OCR backend 做 mock 测试，再在部署环境测试真实 OCR。

### 19.4 文档解析 Slice 依赖

进入 PDF/docx/xlsx 解析时再加入：

```text
pymupdf
python-docx
openpyxl
```

### 19.5 RAG Slice 依赖

进入向量库阶段时再加入：

```text
chromadb
```

如果本地 BGE：

```text
FlagEmbedding
torch
```

或：

```text
sentence-transformers
```

注意：

不要在当前还没进入对应 Slice 时提前加入所有依赖。依赖应随着功能 Slice 分阶段加入。

---

## 20. 部署技术路线

### 20.1 当前部署目标

部署在院内机器。

核心要求：

1. 审计材料不出院。
2. OCR 本地执行。
3. Qwen 本地或院内 endpoint 执行。
4. 后端 FastAPI 本地运行。
5. 前端可以本地 build 后由静态服务器提供，或先用 Vite dev server 演示。
6. 不依赖外部云服务。

### 20.2 最小部署形态

```text
院内机器
  ├── frontend build 静态页面
  ├── FastAPI backend
  ├── PaddleOCR 本地环境
  ├── 本地 Qwen endpoint
  └── 本地 uploads / data 目录
```

### 20.3 本地 Qwen 服务形态

只要本地 Qwen 暴露 OpenAI-compatible endpoint，后端就能接。

推荐目标接口：

```text
http://127.0.0.1:<port>/v1/chat/completions
```

后端配置：

```env
LLM_BASE_URL=http://127.0.0.1:<port>/v1
LLM_MODEL=<local-qwen-model-name>
```

### 20.4 GPU / CPU 策略

当前阶段：

1. OCR 可以先 CPU 测试。
2. Qwen 如果已有本地服务，直接接服务。
3. embedding 后续可先 CPU，小规模制度库可接受。
4. 如果性能不足，再考虑 GPU。

---

## 21. TDD 总原则

从下一阶段开始，项目必须进入 TDD 模式。

TDD 流程是：

```text
Red：先写一个失败测试
Green：写最少代码让测试通过
Refactor：在测试保护下整理代码
```

任何功能开发都必须遵守：

1. 先写测试，后写实现。
2. 测试必须能证明需求被满足。
3. 不允许先写一大堆功能，再补测试。
4. 不允许只写“能跑通”的代码，不写测试。
5. 不允许新增功能没有失败场景测试。
6. 不允许只测试 happy path。
7. 不允许通过降低测试标准让代码通过。

---

## 22. 测试分层

### 22.1 后端单元测试

测试对象：

```text
document_parser.py
ocr_service.py
audit_engine.py
llm_client.py
schemas.py
```

工具建议：

```text
pytest
pytest-asyncio 如需要
FastAPI TestClient
```

### 22.2 后端 API 测试

测试对象：

```text
GET /health
POST /api/analyze
```

要求：

1. `/health` 返回 ok。
2. `/api/analyze` 能接收 txt 文件。
3. `/api/analyze` 能接收多个文件。
4. unsupported 文件不会导致 500。
5. OCR 图片失败不会导致整个请求失败。
6. 没有 `LLM_API_KEY` 时返回 mock。
7. 返回结构符合 `AnalyzeResponse`。

### 22.3 前端测试

当前阶段前端可以先保持轻量测试。

建议后续引入：

```text
vitest
@testing-library/react
```

测试内容：

1. 页面能渲染。
2. 文件选择后列表显示。
3. 输入问题后状态更新。
4. 点击按钮会调用 API。
5. loading 状态显示。
6. 返回结果后展示 `answer_text`。
7. 返回 `parsed_files` 后展示文件解析状态。
8. 错误时显示 error box。

### 22.4 集成测试

集成测试关注完整链路：

```text
前端上传文件
→ 后端接收
→ 后端解析
→ mock LLM
→ 返回 JSON
```

M0 阶段至少要有后端 API 集成测试。

### 22.5 手动验收测试

每个 Slice 完成后必须手动验证：

1. 后端能启动。
2. 前端能启动。
3. `/health` 正常。
4. `/api/analyze` 正常。
5. mock LLM 正常。
6. 前端页面能展示结果。
7. 旧功能没有坏。

---

## 23. 测试目录建议

后端建议新增：

```text
backend/
  tests/
    test_health.py
    test_analyze_api.py
    test_document_parser.py
    test_ocr_service.py
    test_audit_engine.py
    test_llm_client.py
    fixtures/
      sample.txt
      sample.md
      sample.csv
      sample.png
      unsupported.bin
```

前端后续建议新增：

```text
frontend/
  src/
    __tests__/
      App.test.tsx
      api.test.ts
```

---

## 24. 测试覆盖要求

当前阶段不强制追求数字上的 90% 覆盖率。

但必须做到：

1. 每个新增服务模块至少有单元测试。
2. 每个新增 API 至少有 API 测试。
3. 每个 bug fix 必须增加回归测试。
4. 每个 Slice 至少覆盖：
   - 正常路径
   - 失败路径
   - 边界路径
5. parser 类模块必须测试 unsupported / failed。
6. LLM 相关模块必须测试 mock fallback。
7. OCR 模块必须测试 OCR 不可用时不会导致系统崩溃。

建议目标：

```text
后端核心 services 测试覆盖率：>= 70%
新增模块测试覆盖率：>= 80%
```

如果暂时没有覆盖率工具，也必须通过测试用例清单审查。

---

## 25. 当前 Slice 规划

### Slice 0：M0 骨架冻结

状态：已完成。

目标：

```text
前端上传文件
后端接收
txt/md/csv 解析
mock LLM
前端展示
```

应补测试：

1. `/health` test。
2. `/api/analyze` 上传 txt test。
3. unsupported 文件 test。
4. mock LLM test。
5. document_parser txt/md/csv test。

允许修改：

```text
backend/tests/
docs/
```

尽量不改功能代码。

验收：

```bash
cd backend
python -m compileall app
pytest
cd ../frontend
npm run build
```

Commit 建议：

```bash
git commit -m "test(m0): cover scaffold analyze flow"
```

### Slice 1A：图片 OCR 解析

目标：

```text
支持 jpg/png/jpeg/bmp/tiff/webp 图片 OCR
```

允许修改：

```text
backend/requirements.txt
backend/app/services/ocr_service.py
backend/app/services/document_parser.py
backend/app/schemas.py
backend/tests/test_ocr_service.py
backend/tests/test_document_parser.py
backend/tests/test_analyze_api.py
docs/
```

禁止修改：

```text
frontend 大结构
audit_engine 主流程大改
llm_client
vector_retriever
embedding_client
regulation_indexer
ChromaDB
RAG
案例库
数据库
权限系统
```

必须先写的测试：

1. `test_document_parser_returns_ocr_parsed_for_png_when_ocr_succeeds`
2. `test_document_parser_returns_failed_when_ocr_returns_empty_text`
3. `test_document_parser_does_not_break_txt_parsing_after_ocr_added`
4. `test_analyze_api_handles_image_and_txt_mixed_files`
5. `test_ocr_failure_does_not_fail_whole_request`

实现要求：

1. 新增 `ocr_service.py`。
2. `OCRService.extract_text_from_image(path: Path) -> str`。
3. `document_parser.py` 检测图片后缀。
4. OCR 成功返回 `status="ocr_parsed"`。
5. OCR 失败返回 `status="failed"`。
6. 多文件情况下单文件失败不影响整体。
7. OCR 依赖如果不可用，必须 graceful fallback。

验收命令：

```bash
cd backend
python -m compileall app
pytest
```

手动验收：

```text
上传 png/jpg 扫描图片
前端 parsed_files 能看到 ocr_parsed 或清晰 failed
```

Commit 建议：

```bash
git commit -m "feat(parser): add image OCR parsing with tests"
```

### Slice 1B：PDF / docx / xlsx 解析

目标：

```text
支持 PDF / docx / xlsx 文档解析
```

允许修改：

```text
backend/requirements.txt
backend/app/services/document_parser.py
backend/tests/test_document_parser.py
backend/tests/test_analyze_api.py
docs/
```

推荐依赖：

```text
pymupdf
python-docx
openpyxl
```

必须先写测试：

1. PDF 文本型文件解析测试。
2. docx 段落解析测试。
3. docx 表格解析测试。
4. xlsx sheet 解析测试。
5. 不影响 txt/md/csv 测试。
6. 解析失败不导致整个请求 500。

禁止：

```text
不要做扫描 PDF OCR
不要做 ChromaDB
不要做 RAG
不要做前端大改
```

Commit 建议：

```bash
git commit -m "feat(parser): support pdf docx xlsx extraction"
```

### Slice 1C：扫描 PDF OCR

目标：

```text
当 PDF 直接抽取文本很少时，将页面渲染成图片后 OCR
```

允许修改：

```text
backend/app/services/document_parser.py
backend/app/services/ocr_service.py
backend/tests/
docs/
```

必须先写测试：

1. 文本型 PDF 不触发 OCR。
2. 空文本 PDF 触发 OCR fallback。
3. OCR 失败时返回 failed。
4. 多页 OCR 合并文本。
5. 页数过多时有最大页数限制或清晰提示。

Commit 建议：

```bash
git commit -m "feat(parser): add scanned pdf OCR fallback"
```

### Slice 2：部署准备

目标：

```text
让项目可以部署到院内机器
```

允许修改：

```text
README.md
docs/deployment.md
backend/config.py
frontend/vite.config.ts 或部署配置
```

内容：

1. 后端启动方式。
2. 前端 build 方式。
3. 环境变量说明。
4. OCR 依赖安装说明。
5. LLM endpoint 配置说明。
6. 数据不出院说明。
7. 常见故障排查。

禁止：

```text
不要实现 RAG
不要做案例库
不要做权限系统
```

Commit 建议：

```bash
git commit -m "docs(deploy): add hospital machine deployment guide"
```

### Slice 3：制度文档全量向量化

只有在文档解析和 OCR 稳定后再做。

目标：

```text
扫描 data/regulations/raw/
解析制度文件
切 chunk
embedding
写入 ChromaDB
```

必须先有测试：

1. chunk 切分测试。
2. indexer 扫描目录测试。
3. embedding client mock 测试。
4. Chroma 写入可替换或 mock 测试。
5. reindex API 测试。

Commit 建议：

```bash
git commit -m "feat(rag): index regulation documents into vector store"
```

### Slice 4：制度片段检索

目标：

```text
根据上传材料和问题，从向量库检索制度片段
```

必须先有测试：

1. retriever query 测试。
2. top_k 数量测试。
3. 空索引 fallback 测试。
4. retrieved_regulations schema 测试。
5. audit_engine 拼入制度片段测试。

Commit 建议：

```bash
git commit -m "feat(rag): retrieve regulation chunks for audit prompt"
```

### Slice 5：前端展示制度依据

目标：

```text
展示 retrieved_regulations
```

必须先有测试：

1. 有制度片段时展示来源文件。
2. 空制度片段时展示空状态。
3. 长文本片段不破坏页面。

Commit 建议：

```bash
git commit -m "feat(ui): display retrieved regulation chunks"
```

---

## 26. TDD 执行规则：给监督 agent

监督 agent 必须强制 Codex 遵守以下规则。

### 26.1 每次开发前，Codex 必须先说明本次 Slice

Codex 必须输出：

```text
当前 Slice：
目标：
允许修改文件：
禁止修改文件：
新增测试文件：
预期失败测试：
验收命令：
```

如果 Codex 没有先说明这些，不允许它改代码。

### 26.2 每次功能实现前必须先写测试

Codex 必须先做：

```text
新增或修改测试文件
运行测试
确认测试失败
说明失败原因符合预期
```

然后才能写实现代码。

### 26.3 Codex 不允许一次性跨多个 Slice

例如当前做 OCR Slice，就不允许同时做：

- ChromaDB
- embedding
- RAG
- 案例库
- 前端大改
- 权限系统
- 报告导出

### 26.4 每次实现后必须运行测试

至少运行：

```bash
cd backend
python -m compileall app
pytest
```

如果前端被修改，则运行：

```bash
cd frontend
npm run build
```

如果引入前端测试，则运行：

```bash
npm test
```

### 26.5 每次完成后必须输出测试报告

Codex 必须说明：

1. 修改了哪些文件。
2. 新增了哪些测试。
3. 哪些测试先失败。
4. 如何让测试通过。
5. 最终运行了哪些命令。
6. 哪些测试通过。
7. 哪些测试没跑，为什么没跑。
8. 是否修改了 API 契约。
9. 是否新增了依赖。
10. 是否有风险或已知限制。

### 26.6 没有测试不得合并

除非是纯文档修改，否则任何功能代码变更都必须有测试。

例外：

```text
docs/
README.md
注释修正
拼写修正
```

非例外：

```text
新增 OCR
修改 document_parser
修改 main.py
修改 audit_engine
修改 llm_client
修改 schema
修改前端 API 调用
```

这些都必须测试。

---

## 27. Codex 执行模板

每次让 Codex 开发，都必须使用以下模板。

```text
你现在只执行一个 Slice，不允许越界。

当前 Slice：
<填写 Slice 名称>

目标：
<填写目标>

TDD 要求：
1. 先写测试。
2. 运行测试，确认测试失败。
3. 再写最小实现。
4. 再运行测试，确认通过。
5. 最后整理代码。
6. 不允许无测试实现功能。

允许修改文件：
<列出允许文件>

禁止修改文件：
<列出禁止文件>

禁止实现：
<列出禁止功能>

必须新增/更新的测试：
<列出测试文件和测试用例>

验收命令：
<列出命令>

完成后输出：
1. 修改文件列表
2. 新增测试列表
3. 测试失败到通过的过程
4. 最终测试结果
5. 是否新增依赖
6. 是否修改 API 契约
7. 已知限制
8. 下一步建议

如果你发现必须修改允许范围以外的文件，请先停止并说明原因，不要直接修改。
```

---

## 28. 给监督 agent 的审查清单

监督 agent 每次审查 Codex 输出时，必须检查。

### 28.1 范围检查

1. 是否只做了当前 Slice？
2. 是否修改了禁止修改的文件？
3. 是否偷偷实现了未来功能？
4. 是否引入了数据库？
5. 是否引入了 ChromaDB？
6. 是否实现了案例库？
7. 是否做了前端大改？
8. 是否改变了 API 契约？

### 28.2 TDD 检查

1. 是否先写了测试？
2. 是否说明了测试先失败？
3. 是否说明失败原因？
4. 是否实现后测试通过？
5. 是否覆盖失败路径？
6. 是否覆盖边界路径？
7. 是否只写了 happy path？
8. 是否有测试被跳过？
9. 是否通过降低断言标准让测试通过？

### 28.3 架构检查

1. `audit_engine.py` 是否仍然是唯一业务编排者？
2. `llm_client.py` 是否仍然只负责模型调用？
3. `document_parser.py` 是否仍然只负责解析？
4. `ocr_service.py` 是否只负责 OCR？
5. `schemas.py` 是否是唯一 API 契约中心？
6. `main.py` 是否没有膨胀成巨型业务文件？
7. 未来模块是否仍然保持占位或独立？

### 28.4 安全检查

1. 是否把 API key 写进代码？
2. 是否把 `.env` 提交？
3. 是否把上传文件提交？
4. 是否在日志里打印完整材料内容？
5. 是否上传材料到外部服务？
6. 是否允许任意文件类型？
7. 是否有文件名安全处理？
8. 是否处理 OCR 失败？

### 28.5 测试命令检查

必须看到类似：

```bash
cd backend
python -m compileall app
pytest
```

如果前端被改：

```bash
cd frontend
npm run build
```

如果测试没跑，Codex 必须说明原因。

---

## 29. Git 控制要求

每个 Slice 必须单独 commit。

推荐流程：

```bash
git status
git diff
pytest
npm run build
git add .
git commit -m "<message>"
```

重要节点打 tag：

```bash
git tag m0-scaffold
git tag m0-tested
git tag slice-1a-ocr
git tag slice-1b-doc-parser
```

回滚方式：

```bash
git reset --hard <tag_or_commit>
```

Codex 不允许擅自执行 destructive git 命令，例如：

```bash
git reset --hard
git clean -fd
git rebase
```

除非用户明确要求。

---

## 30. 技术风险与应对

### 30.1 PaddleOCR 安装复杂

风险：

1. 依赖较重。
2. 院内机器环境可能不兼容。
3. 模型下载可能失败。

应对：

1. OCRService 做 provider 抽象。
2. 测试中 mock OCR。
3. 文档中记录安装步骤。
4. 提供 `OCR_PROVIDER=disabled` fallback。
5. 必要时使用 Tesseract fallback。

### 30.2 本地 Qwen endpoint 不兼容 OpenAI API

风险：

本地 Qwen 服务可能不是标准 `/chat/completions`。

应对：

1. `llm_client.py` 保持 provider 抽象。
2. 当前先实现 `openai_compatible`。
3. 如不兼容，新增 `qwen_custom` provider。
4. 不改 `audit_engine.py`。

### 30.3 OCR 结果不准确

风险：

扫描件质量差，OCR 错字、漏字。

应对：

1. 输出提示 OCR 可能有误。
2. 保留原文件名。
3. 前端展示 OCR preview。
4. 重要材料需要人工复核。
5. 后续可加入图片预处理。

### 30.4 向量库召回旧制度

风险：

当前 demo 不做制度治理，全量向量化可能召回历史制度。

应对：

1. prompt 提示制度有效性需人工确认。
2. 前端显示来源文件名和 year_hint。
3. 后续客户要求准确性时再做制度治理。

### 30.5 测试依赖大模型导致不稳定

风险：

测试如果依赖真实 Qwen、PaddleOCR、BGE，会慢且不稳定。

应对：

1. 单元测试全部 mock。
2. 真实模型只做手动验收或 optional integration test。
3. CI 不下载大模型。
4. 功能代码允许 provider 注入。

---

## 31. 当前建议的下一步执行顺序

### Step 1：冻结当前 M0 并补测试

目标：

```text
给现有 M0 骨架补测试，不新增功能
```

完成后 commit：

```bash
git commit -m "test(m0): cover scaffold analyze flow"
git tag m0-tested
```

### Step 2：进入图片 OCR Slice

目标：

```text
图片 OCR 解析
```

必须测试先行。

完成后 commit：

```bash
git commit -m "feat(parser): add image OCR parsing with tests"
git tag slice-1a-ocr
```

### Step 3：PDF / Word / Excel 解析

完成后 commit：

```bash
git commit -m "feat(parser): support pdf docx xlsx extraction"
git tag slice-1b-doc-parser
```

### Step 4：部署文档

完成后 commit：

```bash
git commit -m "docs(deploy): add hospital machine deployment guide"
```

### Step 5：本地 Qwen 正式接入

目标：

```text
确认本地 Qwen endpoint
配置 .env
测试 llm_client openai-compatible call
```

### Step 6：制度文档向量化

只有当以下条件满足后再进入：

1. 文档解析稳定。
2. OCR 基本可用。
3. 部署机器能跑。
4. manager 需要制度检索。

技术目标：

```text
BGE-M3 或 bge-small-zh
ChromaDB
regulation_indexer
vector_retriever
```

---

## 32. 当前不允许 Codex 做的事情

在没有用户明确批准前，Codex 不允许：

1. 实现 ChromaDB。
2. 实现 embedding。
3. 实现案例库。
4. 实现权限系统。
5. 实现登录。
6. 实现数据库。
7. 重构整个项目。
8. 重写前端。
9. 改变 `/api/analyze` 返回结构。
10. 删除 mock LLM fallback。
11. 删除现有 txt/md/csv 支持。
12. 把 OCR 结果直接发到外部云 API。
13. 提交真实上传文件。
14. 写死 API key。
15. 一次性实现多个 Slice。
16. 把本地 Qwen 文本模型当作 embedding 模型，除非当前服务明确提供 embedding endpoint。

---

## 33. Definition of Done

一个 Slice 只有同时满足以下条件，才算完成：

1. 功能符合 Slice 目标。
2. 有测试。
3. 测试覆盖正常路径。
4. 测试覆盖失败路径。
5. 测试覆盖边界情况。
6. `python -m compileall app` 通过。
7. `pytest` 通过。
8. 如果改前端，`npm run build` 通过。
9. 没有越界实现未来功能。
10. 没有破坏架构不变量。
11. 没有泄露 API key。
12. 没有提交上传文件。
13. 文档已更新。
14. Codex 输出了修改清单和测试报告。
15. 用户确认后才能 commit。

---

## 34. 最终主线

当前项目的主线必须始终保持简单：

```text
上传文件
  ↓
解析文件 / OCR
  ↓
形成可读文本
  ↓
audit_engine 组织 prompt
  ↓
llm_client 调用 mock 或本地 Qwen
  ↓
返回 AI 初步风险提示
  ↓
前端展示
```

当前不要被未来功能干扰：

```text
制度治理
向量数据库
案例库
报告系统
权限系统
审计闭环
```

这些都不是现在的主战场。

现在的主战场是：

> 让系统可靠地把各种审计材料，尤其是图片和扫描件，变成大模型能读的文字。

---

## 35. 给个人助手 agent 的最终监督指令

你是本项目的开发监督 agent。

你的任务不是亲自写所有代码，而是监督 Codex 按照本文档执行。

你必须始终维护以下原则：

1. 用户掌控感优先。
2. 小步开发优先。
3. 测试先行优先。
4. 架构边界优先。
5. 可回滚优先。
6. 文档同步优先。
7. 不越界实现优先。
8. 技术选型必须按 Slice 分阶段引入。
9. 本地 Qwen 首先作为 LLM，不默认作为 embedding。
10. OCR 和 LLM 优先本地化，避免审计材料外传。

当 Codex 试图一次性做太多功能时，你必须叫停。

当 Codex 没有测试就写功能时，你必须叫停。

当 Codex 修改不该修改的文件时，你必须叫停。

当 Codex 引入新依赖但没有说明理由时，你必须叫停。

当 Codex 破坏 `audit_engine` / `document_parser` / `llm_client` / `ocr_service` 的边界时，你必须叫停。

当 Codex 输出代码后，你必须要求它给出：

```text
修改文件列表
新增测试列表
运行命令
测试结果
是否新增依赖
是否修改 API 契约
是否有已知限制
下一步建议
```

只有当测试通过、范围正确、架构不变、文档更新后，才允许进入下一步。

