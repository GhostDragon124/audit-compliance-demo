# Local Provider Validation

本文件用于院内或本机环境验证 PaddleOCR、Tesseract、本地 Qwen 和离线运行。所有测试数据必须使用非敏感合成材料，不得使用真实审计材料。

## 1. 验证 PaddleOCR

默认测试不会初始化 PaddleOCR，避免首次运行自动下载模型。

先确认模型和依赖已经由院内离线包预置：

- Python 包：`paddleocr`、`paddlepaddle` 或对应平台包。
- 模型目录：确认 PaddleOCR 所需 detection/recognition/classification 模型已经存在本地。
- 网络：不主动断网，但验证时应观察进程不得访问公网。

在确认模型已预置后运行：

```bash
cd /home/spark/workspace/audit-compliance-demo/backend
AUDITPILOT_ALLOW_PADDLEOCR_INIT=1 ../backend/.venv/bin/python -m pytest -m local_ocr
```

记录字段：

- provider：`paddleocr`
- 是否成功：`PASS` / `BLOCKED` / `FAILED`
- 提取字符数：只记录数字，不记录 OCR 全文。
- 关键字段是否识别：只记录 `true/false` 和字段名，不记录完整材料。
- 耗时：秒。
- 错误信息：仅记录依赖或配置错误，不包含材料内容。

注意：

- PaddleOCR 首次初始化可能尝试下载模型。离线部署前必须预置模型并做无公网验证。
- 不得把 PaddleOCR 模型缓存、真实 OCR 图片、OCR 全文提交到 Git。

## 2. 验证 Tesseract

确认系统二进制和中文语言包：

```bash
which tesseract
tesseract --list-langs
```

至少应看到：

- `tesseract` binary 在 PATH。
- 中文简体语言包：`chi_sim`。
- 英文可选：`eng`。

运行：

```bash
cd /home/spark/workspace/audit-compliance-demo/backend
../backend/.venv/bin/python -m pytest -m local_ocr
```

如果缺少依赖，记录为：

```text
BLOCKED: tesseract binary is not installed or chi_sim language pack is missing.
```

建议人工样例：

- 清晰中文打印体图片。
- 旋转图片。
- 模糊图片。
- 无文字图片。
- 简单表格图片。

记录时只写字符数、关键字段是否识别、耗时和错误类别，不写 OCR 全文。

## 3. 验证本地 Qwen

配置文件应位于：

```text
backend/.env
```

示例格式，不要把真实 key 写入文档或提交：

```text
LLM_BASE_URL=http://127.0.0.1:<port>/v1
LLM_API_KEY=<local-secret>
LLM_MODEL=<local-qwen-model>
```

安全检查配置，不输出 key：

```bash
cd /home/spark/workspace/audit-compliance-demo/backend
../backend/.venv/bin/python -c "from app.config import Settings; s=Settings(); print(bool(s.llm_api_key)); print(s.llm_model); print('placeholder' not in s.llm_base_url)"
```

运行验收：

```bash
cd /home/spark/workspace/audit-compliance-demo/backend
../backend/.venv/bin/python -m pytest -m local_qwen
```

需要验证：

- endpoint 可访问。
- `/chat/completions` OpenAI-compatible。
- 模型名正确。
- 正常请求返回中文文本。
- OCR 文本能进入 prompt。
- 多文件内容能进入 prompt。
- 超长输入行为被记录。
- 请求耗时被记录。

当前已知限制：

- 业务代码只把 `preview` 放入 prompt，不能证明完整 OCR 文本进入 Qwen。
- 没有 `LLM_API_KEY` 时会走 mock fallback，不会真实调用 Qwen。
- Qwen 异常响应当前可能导致接口 500。

## 4. 验证离线运行

不要在自动化脚本里主动断网。按以下手动步骤验证：

1. 准备离线依赖包和模型缓存。
2. 确认 `backend/.env` 中所有地址都是 `127.0.0.1`、`localhost` 或院内 IP。
3. 确认 `LLM_BASE_URL` 指向院内 Qwen endpoint。
4. 确认 PaddleOCR 模型已预置；如未预置，设置 `OCR_PROVIDER=tesseract` 或 `OCR_ENABLE=false`。
5. 确认 Tesseract binary 和 `chi_sim` 语言包已安装。
6. 启动后端和前端。
7. 上传非敏感合成样例：txt、pdf、docx、xlsx、图片、扫描 PDF。
8. 观察进程、代理和防火墙日志，确认运行时没有公网连接。
9. 停止服务后检查 `backend/uploads`，确认没有真实材料残留，或按院内策略清理。

运行时外部连接点检查：

- LLM：`LLM_BASE_URL/chat/completions`。
- Embedding：`DEFAULT_OPENAI_COMPATIBLE_BASE_URL=http://localhost:8083/v1`，当前 Slice 2.5 不启用 RAG。
- 前端开发代理：`http://localhost:8000`。
- CORS：`localhost:5173`、`127.0.0.1:5173`。
- 未发现 telemetry、analytics、sentry 运行时代码。

安装期外部连接点：

- `git clone https://github.com/...`
- `frontend/package-lock.json` 中的 npm registry URL。
- Python/npm 依赖安装源。
- PaddleOCR 首次模型下载。

离线部署必须在上线前用院内镜像、离线包或预置缓存替代这些安装期外部连接。

## 5. 如何安全记录结果

允许记录：

- provider 名称。
- 是否成功。
- 文件类型、页数、大小。
- 提取字符数。
- 关键字段是否识别：字段名和布尔值。
- 耗时。
- 错误类别和依赖缺失信息。

禁止记录：

- 真实 API key。
- 真实 Qwen endpoint 中的敏感网段信息，除非院内允许。
- OCR 全文。
- 真实审计材料原文。
- 上传文件保存路径中包含人员、项目、单位敏感信息的部分。
- 模型返回的完整审计材料复述。

## 6. 不得进入 Git 的数据

- `backend/.env`
- `backend/uploads/*`
- 真实审计材料。
- 真实扫描件、截图和 OCR 中间图片。
- OCR 全文结果。
- 本地 Qwen API key、token、鉴权 header。
- 院内 IP、端口、模型服务拓扑等敏感部署细节。
- PaddleOCR/Tesseract 大模型缓存。
- 性能报告中包含的真实材料名称或路径。

当前 `.gitignore` 已覆盖：

```text
backend/.env
backend/uploads/*
!backend/uploads/.gitkeep
```

如新增本地验收输出目录，必须先加入 `.gitignore`，再写入结果。
