# Slice 4c: End-to-End Evaluation

## Goal

实现 Case 001 的完整端到端评估管道：

```text
上传材料
→ 文档解析 / OCR
→ Full Text Flow
→ Embedding
→ ChromaDB 检索
→ Qwen 分析
→ 风险输出与人工复核提示
```

使用真实 Provider（Qwen / PaddleOCR / Embedding）验证 Case 001 的完整闭环。

## Non-goals

- 不改变文档解析逻辑
- 不改变 Full Text Flow
- 不改变 VectorRetriever 接口
- 不改变 API 契约
- 不加入案例库
- 不改变前端

## Required real provider markers

Tests using real providers MUST use the following markers:

- `case001_local_ocr` — for tests requiring real PaddleOCR
- `case001_e2e` — for tests requiring full pipeline (Qwen + Embedding + ChromaDB)

These markers are EXCLUDED from default CI (`addopts` in pytest.ini).

## Case 001 pass criteria

Engineering criteria:
- 所有材料成功解析或返回可解释状态
- OCR 关键字段大部分识别成功
- 无未处理的 500 错误
- retrieved_regulations 包含来源文件与 chunk_id

Retrieval criteria:
- 两份相关制度均进入 Top-5
- 无关差旅费制度不应成为主要依据

Generation criteria:
- 至少指出三个 expected_risk_points
- 不编造制度来源
- 明确提示人工复核

## Required tests

- `backend/tests/evaluation/test_case_001_end_to_end.py`

Tests (all strict xfail with reason `SLICE-4C`):

| Test Name | Target |
|-----------|--------|
| `test_full_pipeline_structure` | 完整管道结构验证 |
| `test_expected_risks_identified` | 至少 3 个预期风险点 |
| `test_no_fabricated_regulation_sources` | 不编造制度来源 |
| `test_no_irrelevant_regulations_as_primary_basis` | 干扰制度不作为主要依据 |
| `test_human_review_prompt_present` | 人工复核提示存在 |
| `test_no_claim_of_final_legal_conclusion` | 不声称最终法律结论 |
| `test_citations_traceable` | 引用可追溯至来源文件 |

## Definition of Done

1. All 7 tests in `test_case_001_end_to_end.py` pass normally (xfail removed)
2. Real PaddleOCR produces usable OCR from 采购审批单_scan.png
3. Real Qwen identifies at least 3 expected risk points
4. No fabricated regulation citations
5. Human review prompt present in output
6. No claim of final legal conclusion
7. Citations are traceable to source_file + chunk_id
8. All pass criteria from Case 001 met

## Status

PROPOSED — requires Project Owner approval before execution
