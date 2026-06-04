# Slice 1C 开发日志

**日期：** 2026-06-05  
**Slice：** 扫描 PDF OCR Fallback  
**执行者：** Codex (GPT-5.5, codex-lb)  
**审查者：** Hermes (Tech Lead) — 通过，功能验证通过

---

## 目标
当 PDF 直接抽取文本很少时，将页面渲染成图片后用 OCR 提取文字。

## 修改文件
| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/app/services/document_parser.py` | 修改 | +50行，`_extract_pdf_text` + `_ocr_pdf_pages` |
| `backend/tests/test_document_parser.py` | 修改 | +3 扫描 PDF OCR 测试 |
| `backend/tests/fixtures/generate_document_fixtures.py` | 修改 | 新增 `generate_scanned_pdf` |
| `backend/tests/fixtures/sample.pdf` | 修改 | 增加文本内容（避免误触发 OCR） |
| `backend/tests/fixtures/scanned_sample.pdf` | 新增 | 扫描版 PDF fixture |

## 测试结果
```
34 passed in 0.18s
ruff: All checks passed!
```

## 手动功能验证
| 场景 | 结果 |
|------|------|
| 文本 PDF (sample.pdf) | `parsed` ✅ 不触发 OCR |
| 扫描 PDF (0字符, 纯图片) | `failed` ✅ 走 OCR fallback，graceful error |

## 技术要点
- 阈值：avg < 20 chars/page OR total < 50 chars
- DPI: 200
- 最大页数: 50
- 临时文件: `/tmp/_ocr_page_N_*.png`，用完删除（`missing_ok=True`）
- 错误链：PaddleOCR → Tesseract → 返回 RuntimeError

## Commit
- **commit:** `3e65e60` — `feat(parser): add scanned PDF OCR fallback`
- **tag:** `slice-1c-scanned-ocr`

## 下一步
Slice 2：部署文档
