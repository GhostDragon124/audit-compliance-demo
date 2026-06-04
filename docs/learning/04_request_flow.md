# 04 一次完整请求流程：从用户点击到页面显示结果

这份文档只讲一件事：用户点击“开始分析”后，数据怎么走。

你可以把它当成 M0 项目的主线地图。

---

## 1. 用户打开网页

用户打开：

```text
http://127.0.0.1:5173/
```

前端页面由 Vite dev server 提供。

相关文件：

```text
frontend/index.html
frontend/src/main.tsx
frontend/src/App.tsx
```

流程：

```text
index.html 提供 root 节点
  ↓
main.tsx 把 App 渲染进去
  ↓
App.tsx 显示页面
```

---

## 2. 用户选择文件

用户点击文件选择区域。

相关代码在：

```text
frontend/src/App.tsx
```

文件 input：

```tsx
<input
  id="files"
  type="file"
  multiple
  accept=".txt,.md,.csv"
  onChange={handleFileChange}
/>
```

触发函数：

```typescript
handleFileChange()
```

它会调用：

```typescript
setFiles(Array.from(event.target.files ?? []));
```

意思是：把用户选中的文件保存到 React 状态 `files` 里。

---

## 3. 用户输入审核问题

用户在 textarea 里输入问题。

相关代码：

```tsx
<textarea
  id="question"
  value={question}
  onChange={(event) => setQuestion(event.target.value)}
  rows={8}
/>
```

每次输入变化，都会调用：

```typescript
setQuestion(event.target.value)
```

意思是：把用户输入的问题保存到 React 状态 `question` 里。

---

## 4. 用户点击开始分析

按钮在：

```text
frontend/src/App.tsx
```

表单绑定：

```tsx
<form onSubmit={handleSubmit} className="analysis-form">
```

用户点击按钮后，执行：

```typescript
handleSubmit()
```

这个函数会：

1. 阻止浏览器默认表单提交。
2. 清空旧错误。
3. 清空旧结果。
4. 检查是否有问题。
5. 检查是否有文件。
6. 设置 loading。
7. 调用后端 API。

---

## 5. frontend 把数据打包成 `FormData`

`handleSubmit()` 调用：

```typescript
analyzeFiles(files, question.trim())
```

`analyzeFiles()` 在：

```text
frontend/src/api.ts
```

它创建：

```typescript
const formData = new FormData();
```

然后打包文件：

```typescript
files.forEach((file) => formData.append("files", file));
```

打包问题：

```typescript
formData.append("question", question);
```

为什么用 FormData？

因为请求里有文件。文件上传不能像普通 JSON 那样简单传字符串。

---

## 6. frontend 调用 backend 的 `/api/analyze`

还是在：

```text
frontend/src/api.ts
```

请求代码：

```typescript
const response = await fetch("/api/analyze", {
  method: "POST",
  body: formData
});
```

因为 `frontend/vite.config.ts` 配了 proxy：

```typescript
proxy: {
  "/api": "http://localhost:8000",
  "/health": "http://localhost:8000"
}
```

所以开发时 `/api/analyze` 会被转发到：

```text
http://localhost:8000/api/analyze
```

---

## 7. backend 接收 multipart/form-data

后端入口在：

```text
backend/app/main.py
```

接口定义：

```python
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    files: list[UploadFile] = File(default=[]),
    question: str = Form(...),
) -> AnalyzeResponse:
```

FastAPI 自动把 multipart/form-data 拆成：

- `files`
- `question`

---

## 8. backend 保存文件

仍然在：

```text
backend/app/main.py
```

核心代码：

```python
safe_name = Path(upload.filename or "uploaded_file").name
saved_name = f"{uuid4().hex}_{safe_name}"
saved_path = UPLOAD_DIR / saved_name

content = await upload.read()
saved_path.write_bytes(content)
```

保存位置：

```text
backend/uploads/
```

---

## 9. backend 解析文件

`main.py` 调用：

```python
parser.parse(saved_path, safe_name)
```

解析逻辑在：

```text
backend/app/services/document_parser.py
```

核心类：

```python
DocumentParser
```

核心方法：

```python
parse()
```

当前支持：

```text
.txt
.md
.csv
```

返回：

```text
ParsedFileSummary
```

---

## 10. backend 调用分析逻辑

`main.py` 创建：

```python
llm_client = LLMClient(settings)
audit_engine = AuditEngine(llm_client=llm_client, prompt_path=PROMPT_PATH)
```

然后调用：

```python
audit_engine.analyze(question=question, parsed_files=parsed_files)
```

分析编排在：

```text
backend/app/services/audit_engine.py
```

它会：

1. 读取 prompt。
2. 把 question 和 parsed_files 拼进 prompt。
3. 调用 `llm_client.chat_completion()`。

LLM 或 mock 逻辑在：

```text
backend/app/services/llm_client.py
```

如果没有 `LLM_API_KEY`：

```python
return self._mock_response(prompt)
```

---

## 11. backend 返回 JSON

`audit_engine.py` 返回：

```python
AnalyzeResponse(
    answer_text=answer_text,
    parsed_files=parsed_files,
    retrieved_regulations=[],
)
```

数据结构定义在：

```text
backend/app/schemas.py
```

FastAPI 会把它变成 JSON。

当前返回形状：

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

---

## 12. frontend 显示结果

`frontend/src/api.ts` 返回：

```typescript
return response.json();
```

`frontend/src/App.tsx` 接收：

```typescript
const response = await analyzeFiles(files, question.trim());
setResult(response);
```

页面展示：

```typescript
result.answer_text
result.parsed_files
result.retrieved_regulations
```

所以用户最终看到：

- AI 初步审核意见
- 文件解析状态
- 制度引用片段空状态

---

## 13. 完整流程图

```text
1. 用户打开网页
   ↓ frontend/index.html
   ↓ frontend/src/main.tsx
   ↓ frontend/src/App.tsx

2. 用户选择文件
   ↓ App.tsx handleFileChange()
   ↓ setFiles()

3. 用户输入审核问题
   ↓ App.tsx textarea onChange
   ↓ setQuestion()

4. 用户点击开始分析
   ↓ App.tsx handleSubmit()

5. frontend 打包数据
   ↓ api.ts analyzeFiles()
   ↓ FormData(files + question)

6. frontend 调用 backend
   ↓ fetch("/api/analyze")
   ↓ Vite proxy
   ↓ FastAPI /api/analyze

7. backend 接收请求
   ↓ backend/app/main.py analyze()

8. backend 保存文件
   ↓ backend/uploads/

9. backend 解析文件
   ↓ document_parser.py DocumentParser.parse()

10. backend 调用分析逻辑
    ↓ audit_engine.py AuditEngine.analyze()
    ↓ llm_client.py LLMClient.chat_completion()

11. backend 返回 JSON
    ↓ AnalyzeResponse

12. frontend 显示结果
    ↓ App.tsx setResult()
    ↓ 页面更新
```

---

## 14. 一句话记忆

```text
App.tsx 收集用户输入，
api.ts 发请求，
main.py 接请求，
document_parser.py 解析文件，
audit_engine.py 编排分析，
llm_client.py 返回 mock 或 LLM 文本，
最后 JSON 回到 App.tsx 展示。
```
