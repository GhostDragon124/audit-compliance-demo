# Slice 2.5 Test Plan

测试日期：2026-06-05

## 1. 测试目标

验证 AuditPilot 当前文档解析、OCR、API、LLM 调用和院内部署链路是否真实可用。范围限定为测试、脚本和文档，不实现 ChromaDB、embedding、RAG、案例库或数据库，不修改 `/api/analyze` API 契约。

重点问题：

- LLM prompt 是否使用完整解析文本，而不是只使用前端 preview。
- 长文档截断是否明确、可见、可测试。
- 图片 OCR、文本 PDF、扫描 PDF、混合 PDF 是否按预期处理。
- 损坏文件、空文件、unsupported 文件、多文件部分失败是否不会导致接口 500。
- 文件数量、大小、PDF 页数、图片尺寸是否有保护。
- OCR provider 是否重复初始化。
- 本地 Qwen endpoint 是否可用，错误时是否优雅失败。
- 离线部署是否存在运行时外部连接、模型下载或敏感数据泄露风险。

## 2. 测试范围

包含：

- `backend/app/schemas.py`
- `backend/app/services/document_parser.py`
- `backend/app/services/audit_engine.py`
- `backend/app/services/llm_client.py`
- `backend/app/services/ocr_service.py`
- `backend/app/main.py`
- `backend/tests/`
- `scripts/run_performance_baseline.py`
- `docs/`
- `.gitignore`
- `frontend` build 验证

不包含：

- ChromaDB/RAG/向量案例库开发。
- 前端页面结构修改。
- 真实审计材料、OCR 全文或院内敏感配置入库。
- 自动下载大型模型。

## 3. 自动化测试清单

| 测试名称 | 测试目的 | 类型 | 涉及文件 | 预期结果 | 当前是否已有覆盖 | 是否需要新增测试 | 是否依赖真实 OCR/Qwen |
|---|---|---|---|---|---|---|---|
| `test_audit_engine_receives_full_text_not_only_preview` | 验证 LLM prompt 是否包含完整解析文本 | UNIT | `document_parser.py`, `audit_engine.py` | 当前 xfail：只包含 preview | 否 | 是 | 否 |
| `test_api_response_does_not_expose_full_sensitive_text` | 验证 API 响应不泄露全文敏感尾部 | API_INTEGRATION/SECURITY | `main.py` | 200，响应不包含全文尾部 | 否 | 是 | 否 |
| `test_long_document_truncation_is_explicit` | 验证长文档截断提示是否明确 | UNIT | `document_parser.py` | 当前 xfail：只有 `...` | 否 | 是 | 否 |
| `test_multiple_parsed_documents_are_included_in_prompt` | 验证多文件均进入 prompt | UNIT | `audit_engine.py` | prompt 包含每个文件名和 preview | 否 | 是 | 否 |
| `test_failed_document_content_is_not_treated_as_valid` | 避免 failed 文件内容被当作有效材料 | UNIT | `audit_engine.py` | 当前 xfail：engine 不按 status 过滤 | 否 | 是 | 否 |
| `test_zero_byte_txt_returns_controlled_result` | 空 txt 不崩溃 | UNIT | `document_parser.py` | `parsed` + 空 preview | 部分 | 是 | 否 |
| `test_empty_document_does_not_crash_request` | 空文件 API 不 500 | API_INTEGRATION | `main.py` | 200，逐文件状态返回 | 部分 | 是 | 否 |
| `test_corrupt_pdf_does_not_crash_request` | 损坏 PDF controlled failure | UNIT | `document_parser.py` | `failed`，有 error | 部分 | 是 | 否 |
| `test_corrupt_docx_does_not_crash_request` | 损坏 DOCX controlled failure | UNIT | `document_parser.py` | `failed`，有 error | 否 | 是 | 否 |
| `test_corrupt_xlsx_does_not_crash_request` | 损坏 XLSX controlled failure | UNIT | `document_parser.py` | `failed`，有 error | 否 | 是 | 否 |
| `test_unsupported_file_does_not_crash_request` | unsupported 文件 API 不 500 | API_INTEGRATION | `main.py` | 200，`unsupported` | 部分 | 是 | 否 |
| `test_mixed_batch_allows_partial_success` | 多文件部分失败不影响其他文件 | API_INTEGRATION | `main.py`, parser | 200，逐文件状态 | 部分 | 是 | 否 |
| `test_filename_path_traversal_is_sanitized` | 路径穿越文件名清理 | SECURITY | `main.py` | 返回 basename | 否 | 是 | 否 |
| `test_duplicate_filenames_do_not_overwrite_each_other` | 同名文件不覆盖 | SECURITY | `main.py` | UUID 保存两份 | 否 | 是 | 否 |
| `test_ocr_success_returns_ocr_parsed` | OCR 成功路径 | UNIT | `document_parser.py` | `ocr_parsed` | 部分 | 是 | mock OCR |
| `test_ocr_empty_text_returns_failed` | OCR 空文本 controlled failure | UNIT | `document_parser.py` | `failed` | 部分 | 是 | mock OCR |
| `test_ocr_exception_does_not_crash_request` | OCR 异常不导致请求崩溃 | UNIT | `document_parser.py` | `failed` | 部分 | 是 | mock OCR |
| `test_mixed_txt_and_failed_image_returns_partial_success` | 图片失败不影响文本 | API_INTEGRATION | `main.py` | 200，部分成功 | 部分 | 是 | mock OCR |
| `test_disabled_ocr_provider_returns_controlled_failure` | OCR disabled controlled failure | UNIT | `ocr_service.py`, parser | `failed` | 部分 | 是 | 否 |
| `test_ocr_provider_not_reinitialized_for_every_file` | 同一 parser 内 OCR provider 不重复初始化 | UNIT | parser | 初始化一次，调用两次 | 否 | 是 | mock OCR |
| `test_text_pdf_does_not_trigger_ocr` | 文本 PDF 不触发 OCR | UNIT | parser | OCR calls 为空 | 已有 | 是 | mock OCR |
| `test_scanned_pdf_triggers_ocr_fallback` | 扫描 PDF 触发 OCR fallback | UNIT | parser | OCR 文本进入 preview | 已有 | 是 | mock OCR |
| `test_scanned_pdf_preserves_page_order` | 扫描 PDF 页面顺序保留 | UNIT | parser | Page 1/2/3 顺序正确 | 否 | 是 | mock OCR |
| `test_mixed_pdf_handles_text_and_scanned_pages` | 混合 PDF 是否逐页 OCR | UNIT | parser | 当前 xfail：不支持逐页混合 | 否 | 是 | mock OCR |
| `test_large_pdf_respects_page_limit` | OCR fallback 页数上限 | UNIT | parser | 只 OCR 前 50 页 | 否 | 是 | mock OCR |
| `test_pdf_partial_processing_is_reported` | 大扫描 PDF 部分处理是否告知用户 | UNIT | parser | 当前 xfail：不报告 | 否 | 是 | mock OCR |
| `test_max_file_count_is_enforced` | 单次最大文件数保护 | SECURITY | `main.py` | 当前 xfail：无保护 | 否 | 是 | 否 |
| `test_max_single_file_size_is_enforced` | 单文件大小保护 | SECURITY | `main.py` | 当前 xfail：无保护 | 否 | 是 | 否 |
| `test_max_total_upload_size_is_enforced` | 总上传大小保护 | SECURITY | `main.py` | 当前 xfail：无保护 | 否 | 是 | 否 |
| `test_image_max_dimensions_are_enforced` | 图片尺寸保护 | SECURITY | `main.py`, parser | 当前 xfail：无保护 | 否 | 是 | 否 |
| `test_llm_mock_fallback_without_api_key` | mock fallback 保留 | UNIT | `llm_client.py` | 无 key 时返回 mock | 已有 | 是 | 否 |
| `test_llm_timeout_returns_controlled_error` | LLM 超时优雅失败 | UNIT | `llm_client.py` | 当前 xfail：异常冒泡 | 否 | 是 | mock HTTP |
| `test_llm_connection_error_returns_controlled_error` | LLM 连接失败优雅失败 | UNIT | `llm_client.py` | 当前 xfail：异常冒泡 | 否 | 是 | mock HTTP |
| `test_llm_http_error_returns_controlled_error` | HTTP 错误优雅失败 | UNIT | `llm_client.py` | 当前 xfail：异常冒泡 | 否 | 是 | mock HTTP |
| `test_llm_invalid_json_returns_controlled_error` | 非法 JSON 优雅失败 | UNIT | `llm_client.py` | 当前 xfail：异常冒泡 | 否 | 是 | mock HTTP |
| `test_llm_missing_choices_returns_controlled_error` | 缺 `choices` 优雅失败 | UNIT | `llm_client.py` | 当前 xfail：异常冒泡 | 否 | 是 | mock HTTP |
| `test_llm_base_url_and_model_come_from_settings` | base url/model 来自配置 | UNIT | `llm_client.py`, config | 通过 | 否 | 是 | mock HTTP |
| `test_api_response_does_not_return_saved_file_path` | 响应不返回保存路径 | SECURITY | `main.py` | 通过 | 否 | 是 | 否 |
| `test_api_response_does_not_return_full_document_text` | 响应不返回全文 | SECURITY | `main.py` | 通过，但说明只返回 preview | 否 | 是 | 否 |
| `test_logs_do_not_include_full_document_content` | 日志不含全文 | SECURITY | app | 通过，当前无业务日志 | 否 | 是 | 否 |
| `test_env_file_is_gitignored` | `.env` 不入 Git | SECURITY | `.gitignore` | 通过 | 部分 | 是 | 否 |
| `test_upload_files_are_gitignored` | 上传文件不入 Git | SECURITY | `.gitignore` | 通过 | 部分 | 是 | 否 |

## 4. 手动测试清单

- 使用真实非敏感样例上传：txt、md、csv、pdf、docx、xlsx、png/jpg。
- 上传损坏 PDF/DOCX/XLSX，确认 `/api/analyze` 返回 200 且逐文件 `failed`。
- 上传混合文件，确认单个失败不会阻断其他文件。
- 上传长文档，确认当前只分析 preview，并记录业务风险。
- 使用扫描 PDF 和混合 PDF，人工确认页面顺序和混合页缺口。
- 检查 `backend/uploads` 是否残留上传文件。
- 在无真实 key 的环境确认 mock fallback 可用。
- 在真实 Qwen 环境确认 timeout、服务关闭、异常响应处理。
- 离线环境中启动前后端，确认没有运行时外网访问或模型下载。

## 5. 本地 Provider 测试清单

默认 `pytest` 不运行真实 provider 测试。

运行 OCR：

```bash
cd backend
../backend/.venv/bin/python -m pytest -m local_ocr
```

运行 Qwen：

```bash
cd backend
../backend/.venv/bin/python -m pytest -m local_qwen
```

PaddleOCR 初始化可能下载模型。只有在模型已经预置且允许初始化时，才设置：

```bash
AUDITPILOT_ALLOW_PADDLEOCR_INIT=1 ../backend/.venv/bin/python -m pytest -m local_ocr
```

## 6. 风险

- P1：LLM prompt 只使用 `preview`，不是完整解析文本。
- P1：长文档截断到 1000 字符且没有明确用户提示。
- P1：真实 LLM 错误会冒泡，可能导致 `/api/analyze` 500。
- P1：缺少文件数量、大小、PDF 总页数、图片尺寸保护。
- P1：上传文件保存在本地且没有请求后清理机制。
- P1：混合 PDF 不支持逐页 OCR，扫描页可能被漏掉。
- P2：PDF OCR fallback 最多 50 页，但部分处理不报告。
- P2：OCR provider 每个请求重新初始化，跨请求不复用。
- P2：PaddleOCR 首次运行可能下载模型，离线部署需预置模型。
- P3：当前环境未安装 `pytest-cov`，覆盖率命令未运行。

## 7. Go / No-Go 标准

进入 Slice 3 前必须满足：

- [ ] 本地 Qwen 可以稳定调用，或明确记录当前阻塞原因。
- [ ] `audit_engine` 使用完整解析文本，而不是仅 preview。
- [ ] 长文档截断行为明确且可见。
- [ ] txt/md/csv/pdf/docx/xlsx/图片解析有真实或合成验收。
- [ ] 扫描 PDF OCR 路径已经验证。
- [ ] 损坏文件不会导致 `/api/analyze` 返回 500。
- [ ] 混合上传支持部分成功。
- [ ] 文件数量、大小和 PDF 页数有保护，或已记录为 P1。
- [ ] OCR provider 不会每个文件重复加载模型。
- [ ] 外部连接点和敏感数据风险已检查。
- [ ] 前端 build 通过。
- [ ] 自动化测试、ruff、CI 通过。

当前存在 P1 问题，测试计划结论为：NO-GO，暂不进入 Slice 3。
