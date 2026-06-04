# Slice 1A 开发日志

**日期：** 2026-06-05  
**Slice：** 图片 OCR 解析  
**执行者：** Codex (GPT-5.5, codex-lb)  
**审查者：** Hermes (Tech Lead) — 通过，不返工

---

## 目标
支持 jpg/png/bmp/tiff/webp 图片 OCR，OCR 失败不崩。

## 修改文件
| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/app/services/ocr_service.py` | 新增 | OCR provider 抽象 (192行) |
| `backend/app/services/document_parser.py` | 修改 | 添加图片后缀检测和 OCR 委托 |
| `backend/app/config.py` | 修改 | 新增 4 个 OCR 配置项 |
| `backend/.env.example` | 修改 | OCR 配置说明 |
| `backend/requirements.txt` | 修改 | 新增 Pillow, pytesseract |
| `backend/tests/test_ocr_service.py` | 新增 | 4 用例 (mock) |
| `backend/tests/test_document_parser.py` | 修改 | +3 图片解析测试 |
| `backend/tests/test_analyze_api.py` | 修改 | +2 API 测试 |
| `backend/tests/fixtures/sample_ocr.txt` | 新增 | OCR 预期文本 |
| `docs/api_contract.md` | 修改 | 文档更新 |
| `docs/architecture_v2_demo_vector.md` | 修改 | 架构文档更新 |

## 测试结果
```
25 passed in 0.04s
ruff: All checks passed!
```

## 审查结论
- Provider 抽象清晰 (4 provider: PaddleOCR/Tesseract/Disabled + Fake)
- 文本提取覆盖 PaddleOCR 新旧版 API 格式 (tuple/dict/list)
- `_parse_image` 覆盖成功/空文本/异常三种路径
- 小建议：`_get_ocr_service()` 的 `get_settings()` 调用可移到 `main.py`

## Commit
- **commit:** `42e74d3` — `feat(parser): add image OCR parsing with tests`
- **tag:** `slice-1a-ocr`

## 已知限制
- PaddleOCR 未在本机安装验证 (ARM64 + PyPI 不可达)
- Tesseract 需要系统 `tesseract` 二进制 + `chi_sim` 语言包

## 下一步
Slice 1B：PDF/docx/xlsx 解析
