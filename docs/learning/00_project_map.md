# 00 项目地图：把 M0 Demo 想象成一家餐厅

这份文档先不讲复杂技术，只帮你建立一张最简单的地图。

当前 M0 项目可以想象成一家小餐厅：

```text
frontend/ = 前厅
backend/ = 后厨
data/ = 仓库
```

前厅负责接待用户，后厨负责处理请求，仓库以后放原材料。现在这家餐厅刚开张，菜单很简单：用户交一份材料和一个审核问题，后厨做一点基础处理，然后返回一份 mock 分析结果。

---

## 1. 这家餐厅现在能做什么

当前 M0 只做一条主线：

```text
用户选择文件
用户输入审核问题
点击开始分析
前端把文件和问题交给后端
后端保存文件
后端解析 txt/md/csv
后端返回 mock 或真实 LLM 结果
前端展示结果
```

它现在不是完整审计系统，也不是完整 RAG 系统。你可以把它理解为“先把餐厅门、点菜台、后厨窗口、出菜流程搭起来”。

---

## 2. 最简单的数据流

```text
用户浏览器
  ↓
React 页面
  ↓
fetch / axios 请求
  ↓
FastAPI API
  ↓
文件解析 / mock LLM
  ↓
JSON 返回
  ↓
前端显示结果
```

当前项目实际使用的是 `fetch()`，没有使用 axios。

---

## 3. 三个核心模块

### frontend/：前厅

前厅就是用户看见和操作的地方。

它负责：

- 显示网页
- 让用户选择文件
- 让用户输入审核问题
- 提供“开始分析”按钮
- 把文件和问题交给后端
- 展示后端返回的分析结果

你第一眼要看的文件是：

```text
frontend/src/App.tsx
frontend/src/api.ts
frontend/src/main.tsx
```

### backend/：后厨

后厨就是接收订单、处理材料、出结果的地方。

它负责：

- 提供 API
- 接收上传文件
- 读取用户问题
- 保存文件到 `backend/uploads/`
- 解析 `.txt`、`.md`、`.csv`
- 调用 `audit_engine`
- 调用 `llm_client`
- 返回 JSON

你第一眼要看的文件是：

```text
backend/app/main.py
backend/app/schemas.py
backend/app/services/document_parser.py
backend/app/services/audit_engine.py
backend/app/services/llm_client.py
```

### data/：仓库

仓库现在基本是空的，但货架已经摆好。

它未来准备放：

- 原始制度文件
- 向量索引
- 示例样本

当前 M0 阶段，你只需要知道它是未来数据边界，不要急着实现 ChromaDB、embedding、RAG。

---

## 4. 主要目录用途

```text
audit-compliance-demo/
```

项目根目录，放前端、后端、数据、文档。

```text
frontend/
```

React + Vite + TypeScript 前端。你在浏览器里看到的页面来自这里。

```text
backend/
```

FastAPI + Python 后端。前端提交文件后，由这里接收和处理。

```text
data/
```

未来放制度、索引、样本的数据边界。当前主要用于学习项目结构。

```text
docs/
```

文档目录。你现在看的学习文档都在这里。

```text
docs/learning/
```

初学者学习路径。建议按编号阅读。

---

## 5. 初学者先不要看哪里

第一轮学习可以先不要看：

```text
frontend/node_modules/
frontend/dist/
backend/.venv/
__pycache__/
```

这些是依赖、构建产物或缓存，不是你理解业务主线的入口。

---

## 6. 一句话记住项目地图

```text
frontend 是前厅，负责接待用户；
backend 是后厨，负责处理请求；
data 是仓库，未来放法规和样本；
M0 只要求你看懂“点菜 -> 后厨处理 -> 出菜展示”这一条线。
```
