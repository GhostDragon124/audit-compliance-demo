# Slice 1B 开发日志

**日期：** 2026-06-05  
**Slice：** PDF / DOCX / XLSX 解析  
**执行者：** Codex (GPT-5.5, codex-lb)  
**审查者：** Hermes (Tech Lead) — 通过，手动功能验证全部通过

---

## 目标
支持 PDF、DOCX、XLSX 文档解析。

## 修改文件
| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/requirements.txt` | 修改 | +PyMuPDF, python-docx, openpyxl |
| `backend/app/services/document_parser.py` | 修改 | +178行，新增 _read_pdf/_read_docx/_read_xlsx 及 XML fallback |
| `backend/tests/test_document_parser.py` | 修改 | +6 PDF/DOCX/XLSX/unsupported doc/unsupported xls/corrupted tests |
| `backend/tests/test_analyze_api.py` | 修改 | +1 PDF API test |
| `backend/tests/fixtures/` | 新增 | sample.pdf/docx/xlsx, unsupported.doc/xls, generate script |
| `docs/api_contract.md` | 修改 | 文档更新 |

## 测试结果
```
31 passed in 0.95s
ruff: All checks passed!
```

## 手动功能验证
| 格式 | 内容 | 结果 |
|------|------|------|
| PDF (fixture) | 英文文本 | `parsed` ✅ |
| PDF (中文) | PyMuPDF 生成 | `parsed` ✅ (缺 CJK 字体导致显示问题，非 parser 问题) |
| DOCX (中文) | 标题+段落+表格 | `parsed` ✅ 全部正确提取 |
| XLSX (中文) | 多 sheet+中文 | `parsed` ✅ 表格格式正确 |
| .doc | 旧格式 | `unsupported` ✅ |
| .xls | 旧格式 | `unsupported` ✅ |

## 审查备注
- Codex 添加了依赖不可用时的 XML 原生解析 fallback（~100行），虽非必需但无害
- PyMuPDF 1.27.2.3, python-docx 1.2.0, openpyxl 3.1.5 均在本机 ARM64 成功安装

## Commit
- **commit:** `d4a4501` — `feat(parser): support pdf docx xlsx extraction`
- **tag:** `slice-1b-doc-parser`

## 下一步
Slice 1C：扫描 PDF OCR fallback
