# 01 前端模块：前厅如何接待用户点菜

`frontend/` 是这个项目的前厅。

用户打开浏览器，看见页面，选择文件，输入审核问题，点击“开始分析”。这些都发生在前端。

你可以把它想象成餐厅前台：

```text
用户 = 客人
上传文件 = 客人带来的材料
审核问题 = 客人点的菜
开始分析按钮 = 下单按钮
api.ts = 把订单送到后厨的服务员
```

---

## 1. 前端入口文件在哪里？

前端入口文件是：

```text
frontend/src/main.tsx
```

它的作用很简单：把主页面 `App` 放进浏览器页面的 `root` 节点里。

你可以理解为：

```text
main.tsx = 前厅开门，把 App 这个主柜台摆到大厅里
```

真正的页面内容不在 `main.tsx`，而在：

```text
frontend/src/App.tsx
```

---

## 2. 页面组件在哪里？

页面组件主要在：

```text
frontend/src/App.tsx
```

这里负责：

- 显示标题
- 显示文件选择框
- 显示审核问题输入框
- 显示开始分析按钮
- 显示 loading 状态
- 显示错误信息
- 显示后端返回的 `answer_text`
- 显示文件解析状态
- 显示制度引用片段空状态

第一天你只要能在 `App.tsx` 里找到这些东西，就已经很好了。

---

## 3. 用户点击“开始分析”后，代码从哪里开始执行？

按钮在 `App.tsx` 里：

```tsx
<button type="submit" disabled={loading} className="primary-button">
```

这个按钮在一个 `<form>` 里面：

```tsx
<form onSubmit={handleSubmit} className="analysis-form">
```

所以用户点击“开始分析”后，会触发：

```text
handleSubmit()
```

文件位置：

```text
frontend/src/App.tsx
```

你可以把 `handleSubmit()` 想象成前台服务员收到订单后开始处理：

1. 检查有没有填写审核问题。
2. 检查有没有选择文件。
3. 显示“正在分析...”。
4. 调用 `analyzeFiles()`。
5. 等后厨返回结果。
6. 把结果展示在页面上。

---

## 4. 前端如何把文件和问题发给后端？

真正发送请求的代码在：

```text
frontend/src/api.ts
```

核心函数是：

```typescript
analyzeFiles(files, question)
```

它会创建：

```typescript
const formData = new FormData();
```

然后把文件放进去：

```typescript
files.forEach((file) => formData.append("files", file));
```

再把审核问题放进去：

```typescript
formData.append("question", question);
```

最后发给后端：

```typescript
fetch("/api/analyze", {
  method: "POST",
  body: formData
})
```

这就像前台服务员把客人的材料和点菜单一起送到后厨窗口。

---

## 5. 前端如何接收后端返回的 JSON？

`api.ts` 里有：

```typescript
return response.json();
```

这表示把后端返回的 JSON 解析成 JavaScript 对象。

然后 `App.tsx` 里接收：

```typescript
const response = await analyzeFiles(files, question.trim());
setResult(response);
```

`setResult(response)` 会把结果保存到 React 状态里。状态变了，页面会自动刷新显示。

当前结果结构大概是：

```text
result.answer_text
result.parsed_files
result.retrieved_regulations
```

---

## 6. 我作为初学者，第一天只需要看哪 2-3 个文件？

第一天只看这三个：

```text
frontend/src/App.tsx
frontend/src/api.ts
frontend/src/main.tsx
```

阅读顺序：

1. 先看 `main.tsx`：知道 App 是怎么被挂载的。
2. 再看 `App.tsx`：知道页面和按钮在哪里。
3. 最后看 `api.ts`：知道前端怎么把订单送到后端。

不要第一天就纠结 CSS、构建配置、TypeScript 细节。

---

## 7. 前台点菜比喻

```text
客人走进餐厅
  ↓
看见前厅页面 App.tsx
  ↓
选择文件，输入审核问题
  ↓
点击开始分析
  ↓
handleSubmit() 接到订单
  ↓
api.ts 用 FormData 打包订单
  ↓
fetch("/api/analyze") 把订单送到后厨
  ↓
后厨返回 JSON 菜品
  ↓
App.tsx 把结果端给客人看
```

---

## 8. 学习任务

```text
学习任务：
只改页面上的一个标题文字，然后运行前端，确认浏览器里发生了变化。
```

建议步骤：

1. 打开 `frontend/src/App.tsx`。
2. 找到：

```tsx
<h1>审计合规智能分析</h1>
```

3. 临时改成：

```tsx
<h1>审计合规智能分析学习版</h1>
```

4. 启动前端：

```bash
cd /home/spark/workspace/audit-compliance-demo/frontend
npm run dev
```

5. 打开浏览器确认标题变化。

做完后你可以再改回来。这个任务的目的不是开发功能，而是让你知道“我改哪个文件，浏览器哪里会变”。
