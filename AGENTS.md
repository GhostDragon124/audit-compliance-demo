# AGENTS.md

> AuditPilot 仓库级 Agent 执行合同  
> 适用对象：Hermes、Codex、Claude Code、ChatGPT、其他自动化开发 Agent  
> 优先级：本文件约束所有 Agent；任何聊天指令如与本文件冲突，必须暂停并向项目 Owner 报告。

---

## 1. 项目一句话定义

AuditPilot 是一个院内部署的审计材料 AI 初步风险筛查 Demo：

```text
上传审计材料
→ 文档解析 / OCR
→ 可选制度检索
→ 本地 LLM 分析
→ 返回初步风险提示与人工复核建议
```

它不是最终审计判定系统，不得将模型输出描述为最终法律或审计结论。

---

## 2. 权力与职责

### Project Owner

项目 Owner 是唯一最终决策者，负责：

- 决定项目目标、范围、优先级和风险接受程度；
- 批准架构变更、API 契约变更和新增大型依赖；
- 决定 Slice 是否完成、是否进入下一阶段；
- 决定是否 commit、tag、merge 或部署。

任何 Agent 不得替 Project Owner 作出上述最终决定。

### Decision Advisors：ChatGPT / Claude

负责：

- 分析需求和架构选择；
- 识别风险、设计验收标准；
- 对重要方案和阶段结果进行独立审查。

Decision Advisors 不直接指挥 Codex；建议必须先由 Project Owner 确认。

### Supervisor：Hermes

负责：

- 将已批准决策拆成单一、有限的 Slice；
- 明确允许修改文件、禁止修改文件、必需测试和验收命令；
- 指挥 Codex 执行；
- 独立检查 Git diff、测试结果、依赖变化和架构边界；
- 发现越界、风险或不确定性时暂停执行并上报。

Hermes 不得擅自扩大需求、改变架构或降低测试标准。

### Executor：Codex

负责：

- 严格按照当前 Slice 执行；
- 先写失败测试，再写最少实现；
- 运行测试、静态检查和构建；
- 输出真实的修改与验证报告。

Codex 不得自行决定产品方向，不得跨 Slice 实现未来功能。

---

## 3. 开工前必须读取

每次开始任务前，Agent 必须按顺序读取：

1. `AGENTS.md`
2. `docs/architecture.md`
3. `docs/governance/README.md`
4. `docs/governance/governance.md`
5. `docs/governance/definition_of_done.md`
6. `docs/governance/current_status.md`
7. `docs/governance/decision_log.md`
8. `current_status.md` 指定的当前 Slice 文件

聊天记录不是最终真相源。仓库内已批准文档优先。

所有治理状态、决策、Slice 和验收证据必须存放在
`docs/governance/` 下。

Agent 不得在 `docs/` 根目录随意创建新的治理文件。

若文档之间冲突，优先级为：

```text
Project Owner 最新明确决策
→ AGENTS.md
→ docs/architecture.md
→ docs/governance/README.md
→ docs/governance/governance.md
→ docs/governance/definition_of_done.md
→ docs/governance/current_status.md
→ docs/governance/decision_log.md
→ 当前 Slice 文件
→ 其他文档和聊天记录
```

发现冲突时，不得自行猜测，必须暂停并报告。

---

## 4. 架构不变量

除非 Project Owner 明确批准，否则不得破坏以下边界：

### `audit_engine`

- 是审计分析流程的唯一业务编排者；
- 负责组织解析结果、检索结果、Prompt 和 LLM 调用；
- 不直接实现 OCR、文件解析、Embedding 或向量数据库细节。

### `document_parser`

- 只负责将文件转换为内部可读文本和解析状态；
- 可以调用 `ocr_service`；
- 不调用 LLM，不判断合规，不执行制度检索。

### `ocr_service`

- 只负责 OCR Provider 生命周期和图片文字提取；
- 不包含审计业务逻辑；
- 不得将材料发送到未批准的外部 OCR 服务。

### `llm_client`

- 只负责模型传输与错误映射；
- 不包含审计 Prompt 和审计业务逻辑；
- 本地 Qwen 无鉴权时不得强制发送 Authorization；
- Mock 与真实模型必须通过显式配置模式选择，不能仅根据 API key 是否为空决定。

### `embedding_client` / `regulation_indexer` / `vector_retriever`

- 分别负责 Embedding、制度索引和向量检索；
- 不调用审计 LLM；
- 不在当前 Full Text Flow 稳定前把 `preview` 当作完整材料接入最终分析；
- Embedding 模型、维度、距离度量或 Chunk 策略变化时，必须重建索引。

### API 契约

- `schemas.py` 是后端 API 数据契约中心；
- API 契约变更必须获得 Project Owner 批准；
- API 不得返回上传文件保存路径、完整敏感材料正文、密钥或院内部署细节；
- 内部完整文本与对外 preview 必须分离。

---

## 5. 数据与安全边界

审计材料默认视为敏感数据。

Agent 必须遵守：

- 不得将真实审计材料、OCR 全文、Prompt 全文或模型完整复述提交到 Git；
- 不得将真实 API key、Token、院内 IP、端口或模型拓扑写入仓库；
- 不得默认调用外部 LLM、OCR、Embedding 或遥测服务；
- 所有真实 Provider 验收必须使用非敏感合成材料，除非 Project Owner 明确批准；
- 日志不得打印完整材料内容；
- 上传文件、`.env`、模型缓存、验收输出必须被 `.gitignore` 覆盖；
- 任何运行时联网、自动下载模型或遥测行为必须显式报告。

本地优先原则：

```text
OCR：优先本地 PaddleOCR
LLM：优先本地 Qwen
Embedding：优先本地或院内服务
向量库：当前优先本地 ChromaDB
```

技术实现不得写死具体端口、模型名、路径或秘密值，应通过配置注入。

---

## 6. 单一 Slice 执行协议

一次任务只能执行一个明确 Slice。

开始前，Hermes 或 Codex 必须输出：

```text
当前 Slice：
目标：
非目标：
允许修改文件：
禁止修改文件：
必须新增或修改的测试：
验收命令：
已知风险：
```

若没有明确 Slice 边界，不得修改代码。

执行期间：

- 不得顺手修复不属于当前 Slice 的问题；
- 不得提前实现后续功能；
- 不得大范围重构；
- 不得改变 API 契约；
- 不得添加未说明的大型依赖；
- 如发现阻塞问题，记录并上报，不得静默扩大范围。

---

## 7. 强制 TDD 流程

除纯文档、注释和拼写修改外，所有业务代码变更必须遵守：

```text
Red
→ 先写或启用能准确描述需求的失败测试

Green
→ 写最少实现使测试通过

Refactor
→ 在全部测试保护下整理代码

Verify
→ 运行完整验收命令并检查 Git diff
```

禁止：

- 先实现功能再补测试；
- 删除、弱化或跳过测试以获得绿色结果；
- 将关键失败测试永久留为非严格 `xfail`；
- 使用 mock 代替必须完成的真实 Provider 验收；
- 只验证 happy path。

每个新增功能至少覆盖：

- 正常路径；
- 失败路径；
- 边界路径；
- 回归路径。

已有 `xfail` 修复后，必须删除 `xfail` 标记并转为正常通过测试。

---

## 8. 默认验证命令

后端发生变化时，至少运行：

```bash
cd backend
python -m compileall app
python -m pytest
ruff check .
```

前端发生变化时，至少运行：

```bash
cd frontend
npm run build
```

若项目已有前端测试，还必须运行相应测试命令。

真实 Provider 测试必须使用独立 marker，不进入默认 CI，例如：

```bash
python -m pytest -m local_ocr
python -m pytest -m local_qwen
python -m pytest -m local_embedding
```

不得伪造未运行、被阻塞或依赖真实环境的测试结果。必须明确标记：

```text
PASS
FAILED
XFAIL
SKIPPED
BLOCKED
NOT_RUN
REQUIRES_MANUAL_VALIDATION
```

---

## 9. Git 与变更控制

默认规则：

- 每个 Slice 使用独立 commit；
- 重要阶段使用 tag；
- 提交前必须检查 `git status` 和 `git diff`；
- 不得提交真实材料、上传文件、模型缓存、`.env` 或敏感验收输出；
- 未经 Project Owner 明确批准，不得执行 destructive Git 命令。

禁止擅自执行：

```bash
git reset --hard
git clean -fd
git rebase
git push --force
git tag -d
```

Codex 不得自行 commit、tag、merge 或 push，除非任务明确授权。

---

## 10. 完成报告格式

每次执行结束，Codex 必须报告：

```text
Slice：
结果：PASS / PARTIAL / BLOCKED / FAILED

修改文件：
新增文件：
删除文件：

新增或修改的测试：
Red 阶段失败证据：
最终测试结果：
运行过的命令：

新增依赖：
API 契约是否变化：
架构边界是否变化：
安全与外部连接风险：
已知限制：
未完成事项：
建议下一步：
Git 状态：
```

Hermes 必须独立验证 Codex 报告，不得只采信口头总结。

---

## 11. 停止条件

出现以下任一情况时，Agent 必须立即停止修改并上报：

- 任务要求与架构文档冲突；
- 必须修改允许范围之外的文件；
- 需要改变 API 契约；
- 需要新增大型依赖或外部服务；
- 发现真实敏感数据可能泄露；
- 测试基线出现无法解释的新失败；
- 需要下载模型或访问公网，但未获得许可；
- 无法证明测试结果真实；
- 当前 Slice 已演变为多个 Slice；
- 需要删除或弱化测试才能继续。

---

## 12. 当前项目特别红线

在 Project Owner 明确批准前：

- 不得把 `preview` 当作完整文档交给最终 LLM 分析；
- 不得无限制地把全文塞入模型，必须遵守上下文预算；
- 不得把 LLM 错误伪装成正常审计结果；
- 不得让上传文件无限残留；
- 不得宣称 Mock OCR / Mock LLM 等同于真实 Provider 验收；
- 不得在真实 Provider 未验收时宣称院内部署可用；
- 不得在基础链路 P1 问题未解决前宣称完整 RAG 已完成；
- Slice 3 基础设施可并行开发，但最终 `audit_engine` 集成需通过 Gate Review。

---

## 13. 面向 Project Owner 的短命令协议

当 Project Owner 使用以下短命令时，Hermes 应按本文件自动展开流程。

### `执行 Slice <编号>`

含义：

- 读取治理、架构、DoD 和对应 Slice 文档；
- 输出执行计划；
- 指挥 Codex 按 TDD 执行；
- 独立验证；
- 返回监督报告；
- 未经批准不进入下一 Slice。

### `审计当前 Slice，禁止修改代码`

含义：

- 只读检查 Git diff、测试、依赖、API 契约、架构边界和风险；
- 不修改实现；
- 输出问题分级和 Go / No-Go 结论。

### `暂停执行，生成决策简报`

含义：

- 停止所有代码修改；
- 整理事实、选项、风险、推荐方案和需要 Owner 决策的问题。

### `通过，更新状态并准备提交`

含义：

- 再次验证 Definition of Done；
- 更新状态和决策文档；
- 准备 commit/tag 建议；
- 未经明确授权不得实际 commit、tag 或 push。

---

## 14. 最终原则

```text
Project Owner 决策
→ Hermes 监督与调度
→ Codex 按 Slice 和 TDD 执行
→ 自动测试与 Git 提供证据
→ Project Owner 批准进入下一阶段
```

优先级永远是：

```text
正确边界
> 可验证性
> 安全与隐私
> 可回滚性
> 开发速度
```

当速度与控制发生冲突时，选择控制。
