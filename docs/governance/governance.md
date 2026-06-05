# AuditPilot Governance

> 文件路径：`docs/governance/governance.md`  
> 文档性质：项目治理规则与决策流程  
> 适用范围：AuditPilot 全部开发、测试、审查、部署与 Agent 协作活动  
> 适用对象：Project Owner、ChatGPT、Claude、Hermes、Codex、其他开发与审查 Agent

---

## 1. 文档目的

本文件定义 AuditPilot 项目如何被治理。

它回答以下问题：

- 谁可以决定项目目标、范围和架构；
- 谁可以拆分和执行开发任务；
- 一个决策如何成为项目正式规则；
- 一个 Slice 如何创建、执行、验收和关闭；
- 多个 Agent 或多个开发轨道如何并行而不互相破坏；
- 测试失败、架构冲突、敏感数据风险出现时如何处理；
- 哪些变更必须由 Project Owner 明确批准；
- 如何让项目事实沉淀在仓库中，而不是散落在聊天记录里。

本文件不负责描述具体代码架构，也不替代：

- `AGENTS.md`
- `docs/architecture.md`
- `docs/governance/definition_of_done.md`
- 单个 Slice 的任务说明

---

## 2. 治理原则

AuditPilot 采用：

```text
Human-led
→ Agent-managed
→ Agent-executed
→ Evidence-verified
```

即：

```text
Project Owner 负责最终决策
→ Hermes 负责监督和调度
→ Codex 负责限定范围内的实现
→ 测试、Git 和文档提供独立证据
```

项目治理优先级：

```text
安全与隐私
> 正确边界
> 可验证性
> 可回滚性
> 可维护性
> 开发速度
```

当快速交付与治理规则冲突时，默认选择治理规则。

---

## 3. 治理角色

## 3.1 Project Owner

Project Owner 是 AuditPilot 的唯一最终决策者。

Project Owner 独占以下权力：

- 批准或拒绝产品目标；
- 批准或拒绝范围扩张；
- 决定当前优先级；
- 批准架构变更；
- 批准 API 契约变更；
- 批准新增大型依赖、外部服务或数据库；
- 批准真实 Provider 初始化和联网行为；
- 批准进入下一 Slice；
- 批准 commit、tag、merge、部署和发布；
- 接受或拒绝已知风险；
- 决定是否暂停项目或回滚。

Project Owner 可以征求任何 Agent 的建议，但最终决策不能由 Agent 自动代替。

---

## 3.2 Decision Advisors

当前 Decision Advisors 包括：

- ChatGPT
- Claude

职责：

- 分析需求、架构与风险；
- 提供备选方案；
- 识别遗漏和潜在失败模式；
- 对重要阶段进行独立审查；
- 帮助 Project Owner形成正式决策。

限制：

- 不直接向 Codex 发布未经过 Project Owner 确认的任务；
- 不自动修改项目事实；
- 不替 Project Owner 批准架构、范围或发布。

---

## 3.3 Supervisor：Hermes

Hermes 是项目监督与调度 Agent。

职责：

- 读取并遵守项目治理文件；
- 将已批准决策拆成有限、可测试的 Slice；
- 明确 Slice 的目标、非目标、允许修改范围和验收标准；
- 指挥 Codex 执行；
- 独立运行测试和检查 Git diff；
- 审查 Codex 是否越界、弱化测试或引入风险；
- 更新状态、决策和监督报告；
- 在出现冲突或风险时暂停执行并上报。

Hermes 不得：

- 擅自改变产品方向；
- 擅自扩大当前 Slice；
- 擅自接受 P0/P1 风险；
- 擅自删除测试；
- 擅自更改架构不变量；
- 擅自 merge、部署或发布。

---

## 3.4 Executor：Codex

Codex 是受限执行 Agent。

职责：

- 按当前 Slice 和 TDD 规则实现代码；
- 只修改允许范围内的文件；
- 运行所需测试和验证命令；
- 输出真实、完整的执行报告；
- 在无法继续时停止并说明原因。

Codex 不拥有：

- 产品决策权；
- 架构审批权；
- 范围扩张权；
- 风险接受权；
- 发布权；
- 最终验收权。

---

## 3.5 Independent Evidence

以下对象不是角色，但被视为独立证据来源：

```text
Git diff
Git history
Automated tests
Static analysis
Build results
CI
CodeQL
Local provider acceptance
Deployment validation
Decision log
Slice reports
```

Agent 的口头总结不能替代这些证据。

---

## 4. 治理文档目录与单一真相源

项目事实不得只存在于聊天记录中。

`docs/governance/` 是 AuditPilot 的治理控制面，用于集中存放治理规则、项目状态、决策日志、Slice 文件和验收证据。

以下仓库文件组成正式真相源：

```text
AGENTS.md
docs/architecture.md
docs/governance/README.md
docs/governance/governance.md
docs/governance/definition_of_done.md
docs/governance/current_status.md
docs/governance/decision_log.md
docs/governance/slices/
docs/governance/acceptance/
```

建议用途：

| 文件 | 作用 |
|---|---|
| `AGENTS.md` | 所有 Agent 的入口执行合同 |
| `docs/architecture.md` | 技术架构与架构不变量 |
| `docs/governance/README.md` | 治理控制面入口、文件职责和读取顺序 |
| `docs/governance/governance.md` | 权力、决策、流程和变更治理 |
| `docs/governance/definition_of_done.md` | Slice 完成标准 |
| `docs/governance/current_status.md` | 当前事实、测试状态、阻塞项和下一步 |
| `docs/governance/decision_log.md` | 已批准的重要决策 |
| `docs/governance/slices/` | 单个 Slice 的正式执行说明目录 |
| `docs/governance/acceptance/` | 验收、Gate Review、真实 Provider 验证和部署验收证据目录 |

低频治理规则文件：

- `docs/governance/governance.md`
- `docs/governance/definition_of_done.md`

高频动态状态文件：

- `docs/governance/current_status.md`
- `docs/governance/decision_log.md`
- `docs/governance/slices/`
- `docs/governance/acceptance/`

重要项目事实只有写入治理控制面后才正式生效。Agent 不得在 `docs/` 根目录随意创建新的治理文件。

聊天中的新决策只有在 Project Owner 明确确认后，才应写入正式文档并生效。

---

## 5. 决策类型

所有重要决策分为四类。

## 5.1 产品与范围决策

示例：

- 是否实现案例库；
- 是否加入制度治理；
- 是否支持某类文档；
- 是否把某功能纳入当前 Demo。

批准者：

```text
Project Owner
```

Agent 可以建议，但不能自行批准。

---

## 5.2 架构决策

示例：

- 引入 ChromaDB；
- 改变 Full Text Flow；
- 修改 `audit_engine` 边界；
- 更换 OCR / Embedding / LLM Provider；
- 修改 API 契约；
- 引入数据库或任务队列。

批准者：

```text
Project Owner
```

建议过程：

```text
Decision Advisor / Hermes 提交决策简报
→ Project Owner 确认
→ 写入 decision_log
→ 更新 architecture 或相关文档
→ 创建对应 Slice
```

---

## 5.3 执行决策

示例：

- 当前 Slice 中函数如何命名；
- 测试 fixture 如何生成；
- 不改变架构的局部实现细节；
- 当前 Slice 内的小型重构。

批准者：

```text
Hermes 可批准
```

前提：

- 不改变架构；
- 不改变 API；
- 不扩展范围；
- 不引入未批准依赖；
- 不影响安全边界。

---

## 5.4 紧急停止决策

任何 Agent 在以下情况可立即暂停执行：

- 发现可能泄露敏感数据；
- 发现测试结果可能被伪造或误报；
- 发现任务与治理文档冲突；
- 发现无法解释的测试基线退化；
- 发现需要联网下载模型但未获批准；
- 发现必须越界修改才能继续；
- 发现 destructive Git 操作风险。

暂停不需要预先批准；恢复执行需要 Project Owner 或 Hermes 在权限范围内明确确认。

---

## 6. 决策生效流程

一个重要决策只有满足以下条件才正式生效：

1. 事实和问题被明确描述；
2. 至少列出一个方案，重要决策应列出多个方案；
3. 风险和影响被说明；
4. Project Owner 明确确认；
5. 决策写入 `docs/governance/decision_log.md`；
6. 如影响架构或治理，相应文档已更新；
7. 后续 Slice 基于该决策创建。

推荐决策记录模板：

```markdown
## D-XXX：决策标题

- 日期：
- 状态：Proposed / Accepted / Superseded / Rejected
- 决策者：Project Owner
- 背景：
- 决定：
- 非目标：
- 原因：
- 风险：
- 影响文件：
- 后续 Slice：
- 替代决策：
```

Agent 不得仅凭“之前聊天里好像同意过”执行重要变更。

---

## 7. Slice 生命周期

每个功能或修复必须尽量作为独立 Slice 管理。

标准生命周期：

```text
Proposed
→ Approved
→ In Progress
→ Verification
→ Owner Review
→ Done / Partial / Blocked / Rejected
```

---

## 7.1 Proposed

Hermes 或 Decision Advisor提出：

- 目标；
- 背景；
- 为什么现在做；
- 依赖和风险；
- 是否与其他 Slice 并行。

此阶段不得修改业务代码。

---

## 7.2 Approved

Project Owner 批准 Slice。

批准后的 Slice 文件至少包含：

```text
Goal
Non-goals
Allowed files
Forbidden files
Required tests
Acceptance commands
Risks
Definition of Done
Rollback plan
```

没有明确边界的任务不得进入执行阶段。

---

## 7.3 In Progress

Codex 按 TDD 执行。

规则：

- 一次只执行一个 Slice；
- 不顺手实现其他需求；
- 不得修改禁止文件；
- 发现阻塞问题时暂停并上报；
- 并行工作必须遵守并行开发规则。

---

## 7.4 Verification

Codex 完成实现后：

- 运行 Slice 测试；
- 运行完整回归测试；
- 运行静态检查和构建；
- 输出执行报告。

Hermes 必须独立验证：

- Git diff；
- 测试结果；
- 依赖变化；
- API 和架构边界；
- 安全风险；
- DoD 完成情况。

---

## 7.5 Owner Review

Project Owner 根据：

- Hermes 监督报告；
- 测试和验收证据；
- 已知风险；
- 是否满足 Definition of Done；

决定：

```text
通过
有条件通过
要求补充
拒绝
回滚
```

Agent 不得自行将 Verification 等同于 Done。

---

## 7.6 Done

只有 Project Owner 明确确认后，Slice 才可标记为 Done。

Done 后应：

- 更新 `docs/governance/current_status.md`；
- 更新相关决策与架构文档；
- 记录测试结果；
- 准备或执行获批的 commit/tag；
- 明确下一步是否开始。

---

## 8. 并行开发治理

AuditPilot 允许并行开发，但必须避免交叉污染。

## 8.1 并行原则

并行 Slice 应满足：

- 目标独立；
- 修改文件尽量不重叠；
- 接口边界已确定；
- 不共享未稳定的内部实现；
- 各自拥有独立测试；
- 有明确最终集成 Gate。

---

## 8.2 并行 Track

当前推荐的并行模式示例：

```text
Track A：Slice 3 索引与检索基础设施
Track B：Full Text Flow、LLM 鲁棒性和上传护栏
```

Track A 可以继续：

- indexer；
- embedding client；
- ChromaDB；
- vector retriever；
- fake embedding 测试；
- local embedding 验收。

Track A 暂时禁止：

- 最终 `audit_engine` 集成；
- 把 preview 当全文；
- 宣称完整 RAG 已完成。

Track B 负责消除基础链路 P1。

最终必须通过统一 Gate Review 后才可集成。

---

## 8.3 并行冲突处理

如果两个 Slice 需要修改同一核心文件：

1. 暂停较低优先级 Slice；
2. Hermes 输出冲突说明；
3. 明确谁拥有该文件的当前修改权；
4. 必要时调整 Slice 边界；
5. Project Owner确认后恢复。

禁止两个 Agent 在未知对方变更的情况下同时修改同一核心文件。

---

## 9. 变更控制

以下变更属于受控变更，必须先批准：

- 修改 `AGENTS.md`；
- 修改治理规则；
- 修改架构不变量；
- 修改 API 契约；
- 修改安全和隐私边界；
- 引入数据库、向量库、队列或外部服务；
- 引入大型依赖；
- 更换 LLM、Embedding 或 OCR 主 Provider；
- 改变索引维度、距离度量或 Chunk 策略；
- 修改关键测试的预期行为；
- 将某个 P1 风险降级或接受。

受控变更流程：

```text
提出变更
→ 分析影响
→ Project Owner 批准
→ 更新文档
→ 新建 Slice
→ TDD 实施
→ Gate Review
```

不得在普通功能 Slice 中偷偷完成受控变更。

---

## 10. 测试与质量治理

TDD 是强制开发模式。

治理要求：

- 新功能必须先有失败测试；
- Bug 修复必须有回归测试；
- 不允许删除或弱化测试来获得绿色结果；
- `xfail` 必须有明确原因、责任 Slice 和严格模式；
- P1 对应 `xfail` 不得长期保留；
- Mock 测试不能替代真实 Provider 验收；
- 普通 CI 与本地真实 Provider 测试应分离；
- 测试数量增加不代表质量自动提高，必须覆盖关键风险。

质量证据至少包括：

```text
pytest
ruff
frontend build
CI
CodeQL
local provider acceptance
manual acceptance
Gate Review
```

---

## 11. 风险分级

所有重要问题按以下等级管理。

### P0：立即停止

示例：

- 敏感数据泄露；
- 破坏性数据丢失；
- 真实密钥进入仓库；
- 未授权外网传输；
- 严重安全漏洞。

处理：

```text
立即停止
→ 上报 Project Owner
→ 禁止继续开发或部署
→ 创建紧急修复与调查
```

---

### P1：进入下一关键阶段前必须修复

示例：

- LLM 只收到 preview；
- 本地 LLM 错误导致接口 500；
- 上传无资源限制；
- 敏感上传文件无限残留；
- 关键真实 Provider 从未验收。

处理：

- 可以允许低耦合基础设施并行；
- 不得通过最终 Gate；
- 必须创建明确修复 Slice。

---

### P2：重要优化

示例：

- OCR provider 跨请求重复初始化；
- PDF partial 未明确报告；
- 部署体验问题。

处理：

- 进入正式部署前应修复；
- 可根据 Demo 需求调整优先级。

---

### P3：后续优化

示例：

- 覆盖率工具未安装；
- 非关键文档完善；
- 工程便利性改善。

处理：

- 进入 backlog；
- 不阻塞当前 Demo。

风险等级只能由 Project Owner 或受权范围内的 Hermes 调整。P0/P1 降级必须由 Project Owner批准。

---

## 12. Gate Review

关键阶段必须进行 Gate Review。

典型 Gate：

```text
文档解析稳定 Gate
本地 Provider 验收 Gate
RAG 最终集成 Gate
院内部署 Gate
Demo 发布 Gate
```

Gate Review 至少检查：

- 所有硬门槛是否满足；
- 是否存在 P0/P1；
- 测试基线是否可信；
- 当前 `xfail` 是否可接受；
- 真实 Provider 是否验收；
- 安全和隐私风险；
- 性能基线；
- 回滚能力；
- 文档是否同步；
- 是否满足 DoD。

Gate 结果：

```text
GO
CONDITIONAL GO
NO-GO
```

只有 Project Owner 能批准 GO 或 CONDITIONAL GO。

---

## 13. 安全与隐私治理

AuditPilot 面向院内审计材料，默认采用最小暴露原则。

治理规则：

- 真实材料默认不得离开院内环境；
- 未经批准不得调用公网 LLM、OCR 或 Embedding；
- Provider 初始化可能联网时必须提前报告；
- `.env`、上传文件、模型缓存和真实验收输出不得入 Git；
- Agent 不得在报告中复述敏感正文；
- 错误日志不得包含完整 Prompt 或材料全文；
- API 响应只返回必要信息；
- 内部完整文本与外部 preview 分离；
- 本地 Provider 验收使用非敏感合成材料。

任何不确定的外部连接行为都视为风险并上报。

---

## 14. Git 与发布治理

### Git

- 每个 Slice 尽量独立 commit；
- 重要节点创建 tag；
- commit 前检查 Git diff；
- 未经批准不得 merge 或 push；
- 禁止提交敏感或运行时产物；
- destructive Git 操作必须由 Project Owner明确授权。

### 发布

任何部署或发布前必须：

- 通过相关 Gate Review；
- 验证当前 commit/tag；
- 验证配置与秘密管理；
- 验证回滚方案；
- 验证真实 Provider；
- 明确当前已知限制；
- 获取 Project Owner批准。

---

## 15. 状态管理

`docs/governance/current_status.md` 应保持简短、事实化。

建议包含：

```markdown
# Current Status

- Current commit:
- Current tag:
- Active tracks:
- Current slice:
- Test baseline:
- P0:
- P1:
- P2:
- Blockers:
- Approved parallel work:
- Forbidden integration:
- Next gate:
- Next owner decision:
```

Hermes 在每个重要 Slice 或 Gate 后负责准备更新，Project Owner确认后生效。

---

## 16. 沟通与短指令

为降低 Project Owner 的输入负担，采用短指令协议。

### `执行 Slice <编号>`

Hermes 应：

- 读取正式文档；
- 输出 Slice 计划；
- 指挥 Codex 按 TDD 执行；
- 独立验证；
- 返回监督报告。

### `审计当前 Slice，禁止修改代码`

Hermes 应只读检查并输出：

- Git diff；
- 测试状态；
- 越界修改；
- 依赖变化；
- 风险分级；
- Go / No-Go 建议。

### `暂停执行，生成决策简报`

Hermes 应停止修改，整理：

- 当前事实；
- 问题；
- 备选方案；
- 风险；
- 推荐方案；
- 需要 Project Owner 决策的问题。

### `通过，更新状态并准备提交`

Hermes 应：

- 重新核验 DoD；
- 更新状态与决策文档；
- 准备提交和 tag 建议；
- 未经明确授权不得实际提交或推送。

---

## 17. 偏离治理规则

如果必须偏离本文件：

1. 明确说明为什么标准流程无法适用；
2. 列出风险；
3. 说明偏离范围和持续时间；
4. 获得 Project Owner 明确批准；
5. 写入 decision log；
6. 在偏离结束后恢复标准流程。

Agent 不得以“任务紧急”为由自行绕过治理。

---

## 18. 治理成功标准

本项目治理被认为有效，当满足：

- Project Owner 不需要反复重写长提示词；
- Hermes 能根据仓库文档自动展开监督流程；
- Codex 不会擅自扩大任务；
- 每个 Slice 都有测试和证据；
- 项目状态可从仓库文档恢复；
- Agent 口头报告可被独立验证；
- 重要决策可追踪；
- 出现问题时能暂停、回滚和定位责任 Slice；
- 敏感数据和 Provider 风险受到控制；
- 并行开发不会破坏核心链路。

---

## 19. 最终治理原则

```text
决策必须显式
范围必须有限
实现必须可测试
结果必须有证据
风险必须可见
变更必须可回滚
最终批准必须由人完成
```
