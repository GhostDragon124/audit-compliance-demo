# Slice 2.9+2.10: Mixed PDF Per-Page OCR & Partial Processing Reporting

> 基线：97 passed / 0 failed / 2 xfailed

## 目标

修复两个 P2 问题：
1. 混合 PDF（部分页文本、部分页扫描）逐页 OCR
2. OCR 页数超限时报告 partial 状态

## 改动清单

### 1. `_read_pdf` 改为逐页判断

当前整份文档平均判断 → 改为逐页：

```python
def _read_pdf(self, file_path: Path) -> str:
    import fitz
    page_texts: list[str] = []
    ocr_pages: set[int] = set()
    
    with fitz.open(str(file_path)) as pdf_document:
        total_pages = len(pdf_document)
        page_limit = min(total_pages, self.pdf_max_pages)
        
        for page_index in range(page_limit):
            page = pdf_document[page_index]
            page_number = page_index + 1
            text = page.get_text().strip()
            
            if len(text) >= 20:          # 文本页
                page_texts.append(f"[Page {page_number}]\n{text}")
            else:                         # 扫描页 → OCR
                ocr_pages.add(page_index)
        
        # OCR 扫描页
        for page_index in sorted(ocr_pages):
            page = pdf_document[page_index]
            page_number = page_index + 1
            text = self._ocr_single_page(page, page_number)
            page_texts.append(f"[Page {page_number}]\n{text}")
    
    result = "\n".join(page_texts)
    if page_limit < total_pages:
        result += f"\n[仅处理前 {page_limit} 页，共 {total_pages} 页]"
    return result
```

### 2. `_ocr_pdf_pages` 添加 partial 提示

在返回前追加：
```python
if page_count < len(pdf_document):
    result += f"\n[仅处理前 {page_count} 页，共 {len(pdf_document)} 页]"
```

### 3. `_extract_pdf_text` 也加 partial

同样逻辑——如果 `pdf_max_pages` 截断了页数。

### 4. 提取 `_ocr_single_page` helper

从 `_ocr_pdf_pages` 中提取单页 OCR 逻辑。

### 5. 测试

- `test_mixed_pdf_handles_text_and_scanned_pages`：xfail → pass
- `test_pdf_partial_processing_is_reported`：xfail → pass
- 已有 97 pass 保持通过

## 验收

```bash
cd backend && python -m pytest -q
# 99+ passed, 0 failed, 0 xfailed
```
