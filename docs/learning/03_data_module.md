# 03 数据模块：仓库暂时空着，但货架已经摆好

`data/` 是这个项目的仓库。

现在仓库里基本没有货，但货架已经摆好了。这样以后项目长大时，我们知道不同东西应该放在哪里。

---

## 1. 为什么 M0 版本 `data/` 现在基本不用？

因为 M0 只做最小闭环：

```text
前端上传文件
后端接收文件
后端解析 txt/md/csv
后端返回 mock 分析结果
前端展示结果
```

这个阶段还不需要：

- 制度库
- 向量索引
- 样本库
- 案例库
- 数据库

所以 `data/` 当前主要是“边界预留”。

---

## 2. `data/regulations/raw/` 未来准备放什么？

目录：

```text
data/regulations/raw/
```

未来准备放原始制度文件。

例如：

```text
data/regulations/raw/
  财务报销管理办法.md
  合同审批制度.pdf
  采购管理制度.docx
```

你可以把它理解成仓库里“法规制度原材料货架”。

当前 M0 不读取这里的文件。

---

## 3. `data/indexes/chroma/regulations/` 未来准备放什么？

目录：

```text
data/indexes/chroma/regulations/
```

未来准备放 ChromaDB 的制度向量索引。

如果用仓库比喻：

```text
data/regulations/raw/ = 原始制度文件
data/indexes/chroma/regulations/ = 把制度处理好之后做成的检索货架
```

未来 RAG 系统可能会这样工作：

1. 读取原始制度文件。
2. 切成小片段。
3. 把每个片段做 embedding。
4. 写入 ChromaDB。
5. 用户提问时，从 ChromaDB 找相关制度片段。

当前 M0 不实现这套流程。

---

## 4. `data/samples/` 未来准备放什么？

目录：

```text
data/samples/
```

未来可以放学习样本或演示样本。

例如：

```text
data/samples/
  sample_invoice.txt
  sample_contract.md
  sample_policy.txt
```

这些文件可以用于：

- 手动测试上传
- 演示项目流程
- 写教程
- 做简单回归测试

当前 M0 没有自动读取 `data/samples/`。

---

## 5. 为什么提前创建 `data/` 是好习惯？

因为它帮你提前划清边界。

如果没有 `data/`，以后你可能会随手把制度文件放到：

```text
backend/
frontend/
docs/
uploads/
```

项目会慢慢变乱。

提前创建 `data/` 的好处：

- 原始数据有固定位置
- 索引数据有固定位置
- 示例样本有固定位置
- 后续做 RAG 时不需要重新想目录结构

这就像餐厅刚开业时，虽然货不多，但先把冷藏区、干货区、调料区分好。

---

## 6. 现在学习阶段应该如何看待 `data/`？

当前你只需要记住：

```text
data/ 是未来的数据仓库，现在基本不参与 M0 主流程。
```

不要因为看到 `chroma` 目录就急着理解 ChromaDB。

现在你只需要知道：

- `raw/` 放未来原始制度
- `chroma/regulations/` 放未来向量索引
- `samples/` 放未来样本文件

---

## 7. 仓库比喻

```text
餐厅刚开业
  ↓
厨房已经能做一道简单菜
  ↓
仓库暂时空着
  ↓
但货架已经贴好标签
  ↓
以后进货时不会乱放
```

---

## 8. 学习任务

```text
学习任务：
在 data/samples/ 里放一个 sample_policy.txt，然后理解它未来可能如何被 backend 读取。
```

建议你手动创建一个文件：

```text
data/samples/sample_policy.txt
```

里面写一点简单内容：

```text
这是一个学习用制度样本。
未来 backend 可能会读取它，用于解析、切 chunk、embedding 和检索。
```

现在 backend 不会自动读取它。这个任务只是帮你理解“样本文件未来应该放在哪里”。
