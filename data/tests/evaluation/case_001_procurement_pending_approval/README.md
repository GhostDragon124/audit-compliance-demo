# Case 001：采购项目未完成审批且采购方式可能不符合规定

这是一个**完全人工构造、非敏感、可提交 Git** 的 AuditPilot 黄金路径测试 Case。

## 测试目标

该 Case 同时验证：

1. Markdown、TXT、XLSX 多文件解析；
2. PaddleOCR 对中文扫描审批单的真实识别；
3. Full Text Flow 与多文件上下文；
4. Embedding + ChromaDB 对相关制度的召回；
5. 无关制度是否被抑制；
6. Qwen 是否能指出预期风险点；
7. 模型是否避免编造制度和最终审计结论；
8. 检索引用是否可以追溯到来源文件和 Chunk。

## 目录

```text
case_001_procurement_pending_approval/
├── README.md
├── question.txt
├── expected_results.yaml
├── materials/
│   ├── 采购项目说明.md
│   ├── 供应商报价.xlsx
│   ├── 采购审批单_scan.png
│   └── 合同草案.txt
├── ground_truth/
│   └── 采购审批单_ground_truth.txt
└── regulations/
    ├── 采购管理办法.txt
    ├── 采购审批管理规定.txt
    └── 差旅费管理规定.txt
```

## 预期业务判断

系统应当识别出：

- 金额达到合成制度中的公开招标标准，但材料显示采用询价采购；
- 未发现非公开招标方式专项审批；
- 财务审批待审批，分管领导未签字；
- 审批尚未完成，但已经确定拟供应商并生成合同草案；
- 仍可能存在未上传材料，需要人工复核。

系统不得：

- 声称已经确认违法或最终不合规；
- 编造不存在的制度、条款编号或来源；
- 将无关的差旅费制度作为主要依据。

## 分阶段使用方式

### Slice 4A：Retriever 接入

只验证：

- `采购管理办法.txt` 和 `采购审批管理规定.txt` 是否进入 Top-5；
- `差旅费管理规定.txt` 是否没有成为主要结果；
- 返回项是否包含 `source_file`、`chunk_id` 和原始片段。

### Slice 4B：RAG Prompt 与引用

验证：

- 正确制度片段进入 Prompt；
- Qwen 使用真实检索来源；
- 不编造制度名称和条款。

### Slice 4C：真实端到端验收

验证：

```text
图文材料上传
→ 文档解析 / OCR
→ Full Text Flow
→ Embedding
→ ChromaDB 检索
→ Qwen 分析
→ 前端展示风险和制度依据
```

## OCR 验收

`ground_truth/采购审批单_ground_truth.txt` 是扫描图片的参考文本。

最低关键字段：

- 实验室服务器采购项目
- 850,000
- 询价采购
- 待审批
- 未签字
- 审批中

无需要求 OCR 全文逐字完全一致，但关键字段应大部分识别成功。

## 注意事项

- 所有内容均为合成测试数据，不代表真实机构制度。
- 制度文件刻意包含一份无关干扰项，用于测试检索质量。
- 第一个 Case 不包含制度版本冲突、手写体或严重模糊图片，以便准确定位问题。
