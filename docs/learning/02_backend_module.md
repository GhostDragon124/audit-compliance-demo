# 02 后端模块：后厨如何接单、处理食材、出菜

`backend/` 是这个项目的后厨。

前端像前厅，负责接待用户；后端像后厨，负责接收订单、处理材料、做出结果。

在这个 M0 项目里，后厨做的事很朴素：

```text
接收文件和问题
保存文件
解析 txt/md/csv
调用 audit_engine
调用 llm_client
返回 JSON
```

---

## 1. FastAPI 入口文件在哪里？

后端入口文件是：

```text
backend/app/main.py
```

这里创建了 FastAPI app：

```python
app = FastAPI(title="Audit Compliance Demo API")
```

你可以把它理解为后厨总入口。所有订单都先到这里。

---

## 2. `/health` 接口在哪里？

`/health` 在：

```text
backend/app/main.py
```

代码是：

```python
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

它的作用是检查后端是否活着。

这就像问后厨：

```text
你们开火了吗？
```

后厨回答：

```json
{"status":"ok"}
```

---

## 3. `/api/analyze` 接口在哪里？

`/api/analyze` 也在：

```text
backend/app/main.py
```

代码入口是：

```python
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    files: list[UploadFile] = File(default=[]),
    question: str = Form(...),
) -> AnalyzeResponse:
```

这是当前最重要的后端接口。

它接收：

- `files`：用户上传的文件
- `question`：用户输入的审核问题

它返回：

- `answer_text`
- `parsed_files`
- `retrieved_regulations`

---

## 4. 后端如何接收上传文件？

关键代码：

```python
files: list[UploadFile] = File(default=[])
```

这告诉 FastAPI：

```text
请求里有一个叫 files 的文件字段，而且可能有多个文件。
```

然后代码会遍历每个文件：

```python
for upload in files:
```

这就像后厨收到一批食材，一份一份处理。

---

## 5. 后端如何读取用户输入的问题？

关键代码：

```python
question: str = Form(...)
```

这告诉 FastAPI：

```text
请求表单里必须有一个 question 字段，它是字符串。
```

前端传来的审核问题会进入这个变量。

---

## 6. 后端如何保存上传文件？

在 `main.py` 中：

```python
safe_name = Path(upload.filename or "uploaded_file").name
saved_name = f"{uuid4().hex}_{safe_name}"
saved_path = UPLOAD_DIR / saved_name

content = await upload.read()
saved_path.write_bytes(content)
```

含义：

1. 取一个安全的文件名。
2. 加上随机 UUID，避免重名。
3. 拼出保存路径。
4. 读取上传内容。
5. 写入 `backend/uploads/`。

这就像后厨把客人带来的食材先贴标签、放到临时工作台。

---

## 7. 后端如何解析文件？

`main.py` 会创建：

```python
parser = DocumentParser()
```

然后调用：

```python
parser.parse(saved_path, safe_name)
```

真正解析逻辑在：

```text
backend/app/services/document_parser.py
```

当前支持：

```text
.txt
.md
.csv
```

不支持的格式不会让整个请求失败，而是返回 `unsupported`。

---

## 8. 后端如何调用 audit_engine？

在 `main.py` 末尾：

```python
settings = get_settings()
llm_client = LLMClient(settings)
audit_engine = AuditEngine(llm_client=llm_client, prompt_path=PROMPT_PATH)
return await audit_engine.analyze(question=question, parsed_files=parsed_files)
```

这几行像后厨把处理好的食材交给主厨：

```text
DocumentParser = 备菜师
AuditEngine = 主厨
LLMClient = 如果需要外部 AI 厨师，就通过它沟通
```

---

## 9. 后端如何返回 JSON？

`audit_engine.analyze()` 返回的是：

```python
AnalyzeResponse
```

定义在：

```text
backend/app/schemas.py
```

FastAPI 会自动把它转换成 JSON 返回给前端。

前端拿到后就能读：

```text
answer_text
parsed_files
retrieved_regulations
```

---

## 10. 后厨比喻完整流程

```text
前厅送来订单
  ↓
main.py 的 /api/analyze 接单
  ↓
读取 question
  ↓
接收 files
  ↓
保存上传文件
  ↓
document_parser.py 备菜
  ↓
audit_engine.py 主厨编排
  ↓
llm_client.py 返回 mock 菜品或真实 LLM 菜品
  ↓
AnalyzeResponse 装盘
  ↓
FastAPI 把结果作为 JSON 端回前厅
```

---

## 11. 初学者第一天只看哪些后端文件？

建议只看：

```text
backend/app/main.py
backend/app/schemas.py
backend/app/services/document_parser.py
```

第二天再看：

```text
backend/app/services/audit_engine.py
backend/app/services/llm_client.py
```

不要一开始就研究 `regulation_indexer.py`、`vector_retriever.py`、`embedding_client.py`，它们现在只是未来占位。

---

## 12. 学习任务

```text
学习任务：
只修改 /health 接口返回的 message 字段，然后运行后端，用浏览器或 curl 确认返回结果发生变化。
```

建议步骤：

1. 打开：

```text
backend/app/main.py
```

2. 找到：

```python
return {"status": "ok"}
```

3. 临时改成：

```python
return {"status": "ok", "message": "backend is running"}
```

4. 启动后端：

```bash
cd /home/spark/workspace/audit-compliance-demo/backend
source .venv/bin/activate
fastapi dev app/main.py
```

5. 测试：

```bash
curl http://127.0.0.1:8000/health
```

6. 观察返回结果。

做完后可以改回去。这个任务的目的不是增加功能，而是让你知道“接口返回值在哪里控制”。
