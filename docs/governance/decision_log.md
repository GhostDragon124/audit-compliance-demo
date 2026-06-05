# Decision Log

## D-001: 建立 docs/governance 治理控制面

- Status: Accepted
- Decision:
  将治理规则、项目状态、决策日志、Slice 文件和验收证据集中存放在 `docs/governance/`。
- Reason:
  避免治理文件散落在 `docs/` 根目录，降低 Agent 读取和项目维护成本。
- Consequences:
  - `AGENTS.md` 保留在仓库根目录；
  - `docs/architecture.md` 保留在 `docs/` 根目录；
  - 治理动态文件统一进入 `docs/governance/`；
  - 必须同步更新旧路径引用。

## D-002: 确认根目录 AGENTS.md 与治理材料归档范围

- Status: Accepted
- Decision:
  根目录 `AGENTS.md` 是正式 Agent 执行合同位置，旧的非根目录 Agent 合同在提交时移除；原 Hermes 计划目录和原测试文档目录中的治理计划、测试计划、验收和 Provider 验证材料统一纳入 `docs/governance/` 管理。
- Reason:
  避免 Agent 入口和 Slice/验收材料分散在多个目录，保证治理控制面可完整恢复项目执行上下文。
- Consequences:
  - 原 Hermes 计划目录中的 Slice 计划进入 `docs/governance/slices/`；
  - 原测试文档目录中的测试计划和 Provider 验证说明进入 `docs/governance/acceptance/`；
  - 后续不得在旧计划目录或旧测试文档目录继续新增正式治理材料；
  - 提交时应保留根目录 `AGENTS.md`，并移除旧 `docs/AGENTS.md`。

## D-003: 建立 Case 001 采购审批黄金测试 Case

- Status: Accepted
- Decision:
  Case 001（采购项目未完成审批且采购方式可能不符合规定）成为 AuditPilot 首个正式黄金测试 Case。
  数据路径：`data/tests/evaluation/case_001_procurement_pending_approval/`（12 个合成非敏感文件，已纳入 Git）。
- Reason:
  需要结构化、可重复的执行验收测试用例，同时覆盖 PDF/OCR/Embedding/检索/RAG/LLM 全链路。
- Consequences:
  - Phase 0 fixture validation（23 tests）全部通过，纳入默认 CI；
  - Slice 4A/4B/4C 测试骨架已创建（17 strict xfail），绑定对应治理文档；
  - 测试代码统一放在 `backend/tests/evaluation/`；
  - Case 数据禁止修改，除非发现明确错误并上报；
  - 未来检索测试必须使用隔离索引，禁止污染正式 ChromaDB collection。

## D-004: PyYAML 纳入显式依赖

- Status: Accepted
- Decision:
  将 `PyYAML` 加入 `backend/requirements.txt` 作为显式一级依赖。
- Reason:
  evaluation 测试框架（`case_001_loader.py`、测试文件）直接 `import yaml` 读取 `expected_results.yaml`，
  PyYAML 不应仅作为 `chromadb`/`paddleocr` 的传递依赖存在。
- Consequences:
  - `requirements.txt` 新增 `PyYAML` 一行；
  - 当前版本 6.0.2，与 `chromadb` 传递依赖版本一致。
  - 后续如需变基 case loader 数据结构，不依赖 PyYAML 特性变更而意外断裂。
