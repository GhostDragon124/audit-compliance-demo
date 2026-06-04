# Slice 0 开发日志

**日期：** 2026-06-05  
**Slice：** M0 骨架测试补齐  
**执行者：** Codex (GPT-5.5, codex-lb)  
**审查者：** Hermes (Tech Lead)

---

## 目标
给 M0 骨架补充后端测试，不新增功能。

## 修改文件
| 文件 | 类型 | 说明 |
|------|------|------|
| `.gitignore` | 修改 | 新增 `.codex` 和法规知识库忽略规则 |
| `backend/tests/conftest.py` | 新增 | 共享 fixtures：client、mock_settings、fixtures_dir |
| `backend/tests/test_health.py` | 新增 | 1 用例 |
| `backend/tests/test_analyze_api.py` | 新增 | 5 用例 |
| `backend/tests/test_document_parser.py` | 新增 | 5 用例 |
| `backend/tests/test_audit_engine.py` | 新增 | 3 用例 |
| `backend/tests/test_llm_client.py` | 新增 | 2 用例 |
| `backend/tests/fixtures/sample.txt` | 新增 | UTF-8 中文测试文本 |
| `backend/tests/fixtures/sample.md` | 新增 | Markdown 测试文件 |
| `backend/tests/fixtures/sample.csv` | 新增 | CSV 测试文件 |
| `backend/tests/fixtures/unsupported.bin` | 新增 | 二进制 unsupported 测试 |

**功能代码修改：** 0 个文件

## 测试结果
```
16 passed in 0.03s
```
- compileall: 通过
- 无跳过、无失败

## 架构检查
- [x] `audit_engine.py` 仍是唯一业务编排者
- [x] `llm_client.py` 只负责模型传输
- [x] `document_parser.py` 只负责文件转文本
- [x] `schemas.py` 是唯一 API 契约中心
- [x] 无新增依赖
- [x] 无 API 契约修改

## Commit
- **commit:** `2f2484d` — `test(m0): cover scaffold analyze flow`
- **tag:** `m0-tested`

## 已知限制
- 测试只覆盖 mock LLM 路径，未覆盖真实 LLM API 调用
- 前端无测试（按 §22.3 后续引入）

## 下一步
Slice 1A：图片 OCR 解析
