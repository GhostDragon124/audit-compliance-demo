# Slice 2.5 Acceptance Report

测试日期：2026-06-05

## 环境

- Git commit：`e0267a134b59a9a559bc4d9010197ddcdd125354`
- Git tag：`slice-3-indexer`
- Python：`Python 3.13.12`
- 操作系统：`Linux spark-c670 6.17.0-1021-nvidia #21-Ubuntu SMP PREEMPT_DYNAMIC Wed May 27 19:14:05 UTC 2026 aarch64`
- 后端测试环境：`backend/.venv`
- `.env`：未发现 `backend/.env`
- 配置状态：`LLM_BASE_URL_CONFIGURED=False`，`LLM_API_KEY_CONFIGURED=False`，`LLM_MODEL_CONFIGURED=True`

## 自动化测试结果

普通测试：

```text
collected 92 items / 5 deselected / 87 selected
73 passed, 5 deselected, 14 xfailed in 5.57s
```

说明：

- 原基线：34 tests。
- 当前收集：92 tests。
- 默认排除：5 个 `local_ocr/local_qwen` 真实 provider 测试。
- xfailed：14 个，均为当前业务缺口的显式验收项。
- 首次直接运行系统 `pytest` 时，因当前 shell 未激活项目 `.venv`，`pytest_asyncio` 缺失，标记为环境问题；后续使用 `backend/.venv` 成功运行。
- `pytest-cov` 未安装，覆盖率命令 `pytest --cov=app --cov-report=term-missing` 标记为 `NOT_RUN`，未安装新依赖。

Ruff：

```text
All checks passed!
```

## 只读架构审查结论

### 完整文本与 preview

- `DocumentParser.parse()` 内部读取 full `content` 后，只返回 `ParsedFileSummary(preview=self._preview(content))`。
- `ParsedFileSummary` 只有 `filename/status/preview/error`，没有 full text 字段。
- `AuditEngine._build_prompt()` 拼入的是 `内容预览`。
- 本地 Qwen prompt 实际收到的是 preview，不是完整解析文本。
- 长文档截断位置：`DocumentParser._preview(content, max_length=1000)`。
- 截断行为：超过 1000 字符返回前 1000 字符加 `...`。
- 用户可在响应中看到 `...`，但没有结构化或自然语言提示说明“仅部分材料被分析”。

结论：P1，进入 Slice 3 前必须修复。

### OCR 生命周期

- `/api/analyze` 每次请求新建 `DocumentParser()`。
- 同一请求内 `DocumentParser._get_ocr_service()` 首次 OCR 时初始化并缓存 provider。
- 同一请求多个图片或 PDF OCR 页不会每个文件重复初始化。
- 跨请求不会复用 OCR provider，真实 PaddleOCR/Tesseract 可能每个请求重新加载。
- OCR 不可用时降级到 `DisabledProvider`；图片解析返回 `failed`，不会直接导致整个请求失败。

结论：同请求复用满足基本要求；跨请求重复初始化为 P2。

### PDF 处理

- 文本 PDF：PyMuPDF `page.get_text()` 逐页抽取，并加 `[Page N]`。
- 扫描 PDF OCR 触发条件：整份 PDF 平均每页字符数 `<20` 或总字符数 `<50`。
- 判断粒度：整份 PDF，不是逐页。
- 混合 PDF：不完整支持。只要整份文本足够，扫描页不会触发 OCR。
- 页面顺序：文本抽取和 OCR fallback 都按页序遍历。
- PDF 最大页数限制：未发现拒绝型限制。
- OCR 最大页数限制：`pdf_ocr_max_pages = 50`。
- 渲染 DPI：固定 `200`。
- 部分处理提示：超过 OCR 页数上限时不会告知用户。

结论：混合 PDF 和部分处理提示为 P1/P2。

### 文件安全与限制

已实现：

- 安全文件名：`Path(upload.filename).name`。
- 路径穿越防护：basename 清理。
- 同名防覆盖：UUID 前缀保存。
- 上传目录 gitignore：`backend/uploads/*`，保留 `.gitkeep`。

未实现：

- 最大单文件大小。
- 最大总上传大小。
- 单次最大文件数量。
- PDF 最大页数拒绝限制。
- 图片最大尺寸。
- 请求后上传文件清理机制。

结论：P1。

### 本地 Qwen

- 使用 OpenAI-compatible `/chat/completions`。
- `LLM_BASE_URL`、`LLM_MODEL` 来自配置。
- 默认 `LLM_BASE_URL` 是占位地址 `http://your-qwen-api-server/v1`。
- timeout 固定为 60 秒，不是配置项。
- mock fallback 保留：无 `LLM_API_KEY` 时返回 mock。
- 未处理：服务关闭、请求超时、HTTP 错误、非法 JSON、缺少 `choices`。

结论：P1。真实 LLM 配置下异常可能导致 `/api/analyze` 500。

## 真实 OCR 验收结果

命令：

```bash
cd backend
../backend/.venv/bin/python -m pytest -m local_ocr
```

结果：

```text
3 selected
1 passed, 2 skipped, 89 deselected
```

记录：

| provider | 是否成功 | 提取字符数 | 关键字段是否识别 | 耗时 | 错误信息 |
|---|---:|---:|---|---:|---|
| Disabled | 成功返回 controlled failure | 0 | 不适用 | 未计量 | 预期 OCRException |
| Tesseract | BLOCKED | 0 | NOT_RUN | 未计量 | `tesseract` binary 不在 PATH |
| PaddleOCR | BLOCKED | 0 | NOT_RUN | 未计量 | 未设置 `AUDITPILOT_ALLOW_PADDLEOCR_INIT=1`，避免首次初始化下载模型 |

清晰中文、旋转、模糊、无文字、表格图片真实识别：`BLOCKED`，当前环境缺少可确认的 Tesseract/PaddleOCR 离线可用配置。

## 本地 Qwen 验收结果

命令：

```bash
cd backend
../backend/.venv/bin/python -m pytest -m local_qwen
```

结果：

```text
2 selected
2 skipped, 90 deselected
```

阻塞原因：

- `backend/.env` 不存在。
- `LLM_API_KEY` 未配置。
- `LLM_BASE_URL` 仍是占位地址。
- 当前机器有 `0.0.0.0:8083` 监听，但项目配置未指向该 endpoint，不能判定为 AuditPilot 已完成本地 Qwen 验收。

验收项状态：

| 验收项 | 状态 |
|---|---|
| endpoint 是否可访问 | BLOCKED |
| `/chat/completions` 是否兼容 | BLOCKED |
| 模型名是否正确 | BLOCKED |
| 正常请求是否返回中文文本 | BLOCKED |
| OCR 文本是否能进入 prompt | BLOCKED，且当前 prompt 只含 preview |
| 多文件内容是否进入 prompt | 自动化 mock 验证通过；真实 Qwen BLOCKED |
| 超长输入如何处理 | BLOCKED；当前业务先截断 preview |
| 请求耗时 | BLOCKED |

## 性能基线

命令：

```bash
backend/.venv/bin/python scripts/run_performance_baseline.py
```

说明：默认使用 synthetic OCR，不触发真实 OCR provider 或模型下载；不含敏感数据；未采集内存指标。

| 文件类型 | 文件大小 | 页数 | 解析状态 | 解析耗时 | OCR 耗时 | LLM 耗时 | 总耗时 | 错误 |
|---|---:|---:|---|---:|---:|---:|---:|---|
| single_image_ocr | 1409 B | - | ocr_parsed | 0.0000s | N/A | N/A | 0.0000s | 无 |
| text_pdf | 876 B | 1 | parsed | 0.0052s | N/A | N/A | 0.0052s | 无 |
| single_page_scanned_pdf | 518 B | 1 | parsed | 0.0574s | N/A | N/A | 0.0574s | 无 |
| ten_page_scanned_pdf | 1970 B | 10 | parsed | 0.4991s | N/A | N/A | 0.4991s | 无 |
| docx | 36771 B | - | parsed | 0.0047s | N/A | N/A | 0.0047s | 无 |
| xlsx | 4893 B | - | parsed | 0.0026s | N/A | N/A | 0.0026s | 无 |
| five_image_batch | - | - | parsed | 0.0058s | N/A | N/A | 0.0058s | 无 |
| mixed_upload_parse_loop | - | - | parsed | 0.0577s | N/A | N/A | 0.0577s | 无 |

## 安全检查结果

日志：

- 未发现业务 logger/print 输出全文材料。
- 自动化测试 `test_logs_do_not_include_full_document_content` 通过。

API 响应：

- 不返回保存路径。
- 不返回 full text，只返回 preview。
- 但这同时导致 LLM 也只收到 preview，是业务完整性风险。

Git ignore：

- `backend/.env` 已忽略。
- `backend/uploads/*` 已忽略，保留 `.gitkeep`。

外部连接点：

- 运行时 LLM：`backend/app/config.py` 默认 `http://your-qwen-api-server/v1`，真实调用时访问 `{LLM_BASE_URL}/chat/completions`。
- 运行时 embedding：`backend/app/services/embedding_client.py` 默认 `http://localhost:8083/v1`，但本次未实现或启用 RAG。
- 前端开发代理：`frontend/vite.config.ts` 指向 `http://localhost:8000`。
- CORS：`http://localhost:5173`、`http://127.0.0.1:5173`。
- 文档中的 GitHub clone URL 是安装期外部连接。
- `frontend/package-lock.json` 包含 registry URL，是安装期依赖来源，不是运行时访问。
- 未发现 telemetry、analytics、sentry 运行时代码。

敏感数据：

- 未发现真实 API key 输出。
- 未发现 `backend/.env` 文件。
- 当前机器存在 `data/regulations/raw/知识库/` 路径并被 `.gitignore` 部分覆盖；本次未读取或提交真实材料。

## 发现的问题

| 等级 | 问题 | 涉及文件 | 推荐修复 | 建议后续 Slice |
|---|---|---|---|---|
| P1 | LLM 只收到 preview，不收到完整解析文本 | `schemas.py`, `document_parser.py`, `audit_engine.py` | 引入内部 full text 载体，响应仍只返回 preview；prompt 使用 full text 或显式 chunk | Slice 2.6 Full Text Flow |
| P1 | 长文档截断为 1000 字符且提示不明确 | `document_parser.py` | 返回结构化 `truncated/original_chars/used_chars`，answer 明确部分分析 | Slice 2.6 Full Text Flow |
| P1 | LLM timeout/连接/HTTP/JSON/choices 错误会冒泡 | `llm_client.py`, `main.py` | 捕获异常并返回 controlled error，保留 mock fallback | Slice 2.7 LLM Robustness |
| P1 | 缺少文件数量、大小、总量、PDF 页数、图片尺寸保护 | `main.py`, parser | 添加配置化限制和 4xx 错误，不改 API 成功响应契约 | Slice 2.8 Upload Guardrails |
| P1 | 上传文件请求后不清理 | `main.py` | 使用 `try/finally` 清理临时上传，或配置安全保留策略 | Slice 2.8 Upload Guardrails |
| P1 | 混合 PDF 不逐页 OCR，扫描页可能漏检 | `document_parser.py` | 逐页判定文本密度，缺文本页单页 OCR 后合并 | Slice 2.9 Mixed PDF OCR |
| P2 | PDF OCR 只处理前 50 页但不报告 partial | `document_parser.py` | 在解析摘要中报告 partial/page_limit | Slice 2.9 Mixed PDF OCR |
| P2 | OCR provider 跨请求重复初始化 | `main.py`, `ocr_service.py` | app lifespan 或 dependency singleton 管理 provider | Slice 2.10 OCR Lifecycle |
| P2 | PaddleOCR 首次运行可能下载模型 | `ocr_service.py`, deployment docs | 院内部署预置模型目录，并离线验证 | Slice 2.10 OCR Lifecycle |
| P2 | 默认 `LLM_BASE_URL` 是占位外部样式地址 | `config.py`, `.env.example` | demo 默认继续 mock；真实部署强制 `.env` 指向内网 | Slice 2.7 LLM Robustness |
| P3 | `pytest-cov` 未安装，覆盖率命令未运行 | test config | 如需要覆盖率，加入 dev requirements | Slice 2.x Test Tooling |

未发现 P0。

## Go / No-Go 结论

NO-GO：暂不进入 Slice 3。

原因：

- 存在多个 P1，尤其是 LLM 只收到 preview、长文档静默截断、LLM 错误可能导致 500、缺少上传限制、混合 PDF 不完整支持。
- 本地 Qwen 真实验收 `BLOCKED`。
- 真实 OCR 验收仅 disabled provider controlled failure 通过，Tesseract/PaddleOCR 真实识别 `BLOCKED`。

满足进入 Slice 3 前，建议先完成：

1. Slice 2.6：Full Text Flow and Explicit Truncation。
2. Slice 2.7：LLM Robustness and Local Qwen Acceptance。
3. Slice 2.8：Upload Guardrails and Cleanup。
4. Slice 2.9：Mixed PDF Per-page OCR。
5. Slice 2.10：OCR Lifecycle and Offline Model Validation。
