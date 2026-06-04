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

Unsupported formats return a file-level `unsupported` status and do not fail the entire request.

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
