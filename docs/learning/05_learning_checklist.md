# M0 学习清单

这份清单不是考试。它的目标是让你每天只掌控一小块。

建议你不要第一天就试图理解所有代码。先知道地图，再看前端，再看后端，再看前后端连接。

---

## 第 1 天：只看项目地图

- [ ] 我知道 `frontend/` 是前厅
- [ ] 我知道 `backend/` 是后厨
- [ ] 我知道 `data/` 是仓库
- [ ] 我知道 `docs/learning/` 是学习路径
- [ ] 我知道 M0 阶段只做一条主线
- [ ] 我知道现在不需要理解 ChromaDB、embedding、RAG

建议阅读：

```text
docs/learning/00_project_map.md
```

---

## 第 2 天：只看 `frontend/`

- [ ] 我能找到前端入口 `frontend/src/main.tsx`
- [ ] 我能找到页面组件 `frontend/src/App.tsx`
- [ ] 我能找到文件选择 input
- [ ] 我能找到“开始分析”按钮
- [ ] 我能找到 `handleSubmit()`
- [ ] 我能找到调用后端 API 的代码 `frontend/src/api.ts`
- [ ] 我知道 `FormData` 用来打包文件和问题
- [ ] 我知道前端展示结果来自 `result`

建议阅读：

```text
docs/learning/01_frontend_module.md
frontend/src/main.tsx
frontend/src/App.tsx
frontend/src/api.ts
```

---

## 第 3 天：只看 `backend/`

- [ ] 我能找到 FastAPI app：`backend/app/main.py`
- [ ] 我能找到 `/health`
- [ ] 我能找到 `/api/analyze`
- [ ] 我知道 `files` 来自上传文件
- [ ] 我知道 `question` 来自用户输入
- [ ] 我知道上传文件保存到 `backend/uploads/`
- [ ] 我知道文件解析在 `document_parser.py`
- [ ] 我知道分析编排在 `audit_engine.py`
- [ ] 我知道 mock LLM 在 `llm_client.py`
- [ ] 我知道返回结构在 `schemas.py`

建议阅读：

```text
docs/learning/02_backend_module.md
backend/app/main.py
backend/app/schemas.py
backend/app/services/document_parser.py
```

---

## 第 4 天：理解前后端连接

- [ ] 我知道前端如何调用后端
- [ ] 我知道 `fetch("/api/analyze")` 是发送 HTTP 请求
- [ ] 我知道 Vite proxy 会把 `/api` 转到后端
- [ ] 我知道后端接收的是 multipart/form-data
- [ ] 我知道后端返回的是 JSON
- [ ] 我知道浏览器里看到的结果来自后端 response
- [ ] 我能画出一次完整请求流程

建议阅读：

```text
docs/learning/04_request_flow.md
frontend/src/api.ts
backend/app/main.py
```

---

## 第 5 天：理解 `data/`

- [ ] 我知道 `data/` 现在大部分只是预留
- [ ] 我知道未来法规文件可以放在 `data/regulations/raw/`
- [ ] 我知道未来向量索引可以放在 `data/indexes/chroma/regulations/`
- [ ] 我知道未来样本可以放在 `data/samples/`
- [ ] 我知道当前 M0 不会自动读取 `data/samples/`
- [ ] 我知道提前创建 `data/` 是为了保持数据边界清晰

建议阅读：

```text
docs/learning/03_data_module.md
```

---

## 第 6 天：亲手做最小改动

- [ ] 我能只改一个前端标题
- [ ] 我能启动前端看到变化
- [ ] 我能只改 `/health` 的返回内容
- [ ] 我能启动后端看到变化
- [ ] 我知道这些练习只是学习，不是新增业务功能
- [ ] 我知道练习后可以用 Git 恢复

建议命令：

```bash
git status
git diff
```

如果只是学习改动，想丢弃：

```bash
git checkout -- frontend/src/App.tsx backend/app/main.py
```

---

## 第 7 天：复述 M0 主线

- [ ] 我能说出 `App.tsx` 做什么
- [ ] 我能说出 `api.ts` 做什么
- [ ] 我能说出 `main.py` 做什么
- [ ] 我能说出 `document_parser.py` 做什么
- [ ] 我能说出 `audit_engine.py` 做什么
- [ ] 我能说出 `llm_client.py` 做什么
- [ ] 我能解释为什么没有 API key 也能返回 mock
- [ ] 我能解释为什么 `retrieved_regulations` 现在是空数组

最终目标：

```text
我知道 frontend 点击按钮后，
数据如何经过 backend，
再以 JSON 回到 frontend 显示。
```
