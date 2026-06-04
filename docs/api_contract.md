# API Contract

## GET `/health`

Response:

```json
{
  "status": "ok"
}
```

## POST `/api/analyze`

Request type: `multipart/form-data`

Fields:

- `files`: one or more uploaded files.
- `question`: audit question entered by the user.

Supported parser formats in M0+:

- `.txt`
- `.md`
- `.csv`
- `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`, `.webp` through OCR

File-level statuses:

- `parsed`: text/markdown/csv parsed successfully.
- `ocr_parsed`: image OCR parsed successfully.
- `unsupported`: file suffix is not supported.
- `failed`: parsing or OCR failed for this file. Other uploaded files continue processing.

Response:

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
