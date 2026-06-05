# Slice 2.8: Upload Guardrails & Cleanup

> 基线：89 passed / 0 failed / 6 xfailed

## 目标

实现上传资源保护：大小限制、数量限制、请求结束后的文件清理。

## 改动清单

### 1. Config 新增

```python
max_file_size_mb: int = 50
max_total_upload_mb: int = 100
max_files_per_request: int = 10
pdf_max_pages: int = 100
image_max_pixels: int = 50_000_000   # ~50 megapixels
upload_cleanup: bool = True           # 请求结束后清理上传文件
```

### 2. main.py 上传校验

在 `analyze` 路由中，文件保存前校验：

```python
# 文件数量限制
if len(files) > settings.max_files_per_request:
    raise HTTPException(400, f"单次最多上传 {settings.max_files_per_request} 个文件")

total_size = 0
for upload in files:
    content = await upload.read()
    total_size += len(content)
    # 单文件大小限制
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(413, f"单个文件最大 {settings.max_file_size_mb} MB")
    # 图片尺寸限制 (Pillow)
    if suffix in SUPPORTED_IMAGE_SUFFIXES:
        img = Image.open(io.BytesIO(content))
        if img.width * img.height > settings.image_max_pixels:
            raise HTTPException(413, "图片尺寸过大")

# 总上传大小限制
if total_size > settings.max_total_upload_mb * 1024 * 1024:
    raise HTTPException(413, f"单次上传总大小最大 {settings.max_total_upload_mb} MB")
```

### 3. PDF 页数限制

在 `_extract_pdf_text` 中：超过 `pdf_max_pages` 的页不处理（或抛错）。

### 4. 请求结束后清理

```python
try:
    result = await audit_engine.analyze(...)
finally:
    if settings.upload_cleanup:
        for saved_path in saved_paths:
            saved_path.unlink(missing_ok=True)
```

或使用 `tempfile` 临时目录自动清理。

### 5. 测试

- `test_max_file_count_is_enforced`：xfail → pass
- `test_max_single_file_size_is_enforced`：xfail → pass
- `test_max_total_upload_size_is_enforced`：xfail → pass
- `test_image_max_dimensions_are_enforced`：xfail → pass
- 新增 `test_upload_cleanup_removes_files`：验证请求完成后文件被删除
- 不修改已有通过测试

## 验收

```bash
cd backend && python -m pytest -q
# 预期：93 passed / 0 failed / 2 xfailed
```
