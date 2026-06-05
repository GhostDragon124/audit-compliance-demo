# AuditPilot Definition of Done

> 文件路径：`docs/governance/definition_of_done.md`  
> 文档性质：完成定义与验收门槛  
> 适用范围：所有 Slice、Bug 修复、架构变更、真实 Provider 验收、RAG 集成与部署活动  
> 适用对象：Project Owner、Hermes、Codex、Claude Code、其他开发与审查 Agent

---

## 1. 文档目的

本文件定义：

> 一个任务、一个 Slice 或一个阶段，在什么条件下才真正算完成。

“代码写完了”“测试大部分通过”“Codex 说完成了”“页面能打开”都不等于 Done。

AuditPilot 的 Done 必须建立在：

```text
范围正确
+ 功能正确
+ 测试充分
+ 架构未破坏
+ 安全风险可接受
+ 文档同步
+ 可验证
+ 可回滚
+ Project Owner 明确批准
```

之上。

---

## 2. Done 的状态定义

任何任务只能处于以下状态之一：

### `DONE`

满足本文件全部适用门槛，并经 Project Owner 明确批准。

### `CONDITIONAL_DONE`

核心目标已完成，但仍有被明确接受的非阻塞问题。

要求：

- 所有遗留问题已记录；
- 风险等级已确认；
- 有明确后续 Slice；
- Project Owner 明确接受风险。

### `PARTIAL`

只完成了部分目标，不能宣称 Slice 完成。

### `BLOCKED`

由于环境、依赖、真实 Provider、权限或外部条件无法继续。

### `FAILED`

实现或验收不满足要求，且当前没有可接受的完成路径。

### `REJECTED`

实现方向、范围或风险不可接受，被 Project Owner 拒绝。

未经 Project Owner 明确批准，Agent 不得将任何任务标记为 `DONE` 或 `CONDITIONAL_DONE`。

---

## 3. 通用 Definition of Done

除纯文档任务外，任何 Slice 要达到 Done，必须满足以下全部适用条件。

---

## 3.1 范围与目标

- [ ] Slice 目标清晰且已经实现；
- [ ] 非目标没有被偷偷实现；
- [ ] 没有跨 Slice 扩张；
- [ ] 只修改了允许范围内的文件；
- [ ] 如必须越界修改，已提前获得批准；
- [ ] 所有新增行为均有明确需求来源；
- [ ] 当前结果与已批准决策一致；
- [ ] 未遗留无法解释的隐式行为。

不满足任一项：

```text
不得标记 DONE
```

---

## 3.2 TDD 与测试

- [ ] 新功能先有失败测试；
- [ ] Bug 修复先有回归测试；
- [ ] 测试失败原因与需求一致；
- [ ] 实现后测试转为通过；
- [ ] 正常路径已覆盖；
- [ ] 失败路径已覆盖；
- [ ] 边界路径已覆盖；
- [ ] 回归路径已覆盖；
- [ ] 未删除、弱化或跳过测试以获得绿色结果；
- [ ] 新增 `xfail` 有明确原因、责任 Slice 和严格模式；
- [ ] 已修复问题对应的 `xfail` 已转为正常通过；
- [ ] 普通测试无无法解释的失败；
- [ ] 测试结果可以被 Hermes 独立复现。

最低要求：

```text
0 unexpected failed tests
0 unexplained skipped tests
0 unexplained xfailed tests
```

真实 Provider 被阻塞时，可以保留明确的 `BLOCKED`，但不得伪装成通过。

---

## 3.3 默认自动化验证

后端有变化时，至少通过：

```bash
cd backend
python -m compileall app
python -m pytest
ruff check .
```

前端有变化时，至少通过：

```bash
cd frontend
npm run build
```

若已引入前端测试，还必须通过对应测试命令。

CI 存在时：

- [ ] CI 通过；
- [ ] CodeQL 或其他安全检查无新增高风险问题；
- [ ] 本地与 CI 结果无无法解释的差异；
- [ ] 测试基线与报告一致。

如果某命令无法执行，必须标记：

```text
NOT_RUN / BLOCKED
```

并说明原因。未运行的必要验证会阻止 Done。

---

## 3.4 架构边界

- [ ] `audit_engine` 仍是唯一业务编排者；
- [ ] `document_parser` 只负责解析；
- [ ] `ocr_service` 只负责 OCR；
- [ ] `llm_client` 只负责模型传输与错误映射；
- [ ] `embedding_client`、`regulation_indexer`、`vector_retriever` 职责未混杂；
- [ ] `main.py` 没有膨胀成业务巨型文件；
- [ ] 内部完整文本与外部 preview 分离；
- [ ] 没有把 `preview` 当完整材料用于最终分析；
- [ ] 没有绕过配置写死端口、模型名、路径或密钥；
- [ ] 没有未经批准修改 API 契约；
- [ ] 没有未经批准改变索引或数据模型。

如架构边界发生变化：

```text
必须先有批准的架构决策
→ 更新 architecture / decision log
→ 再实施
```

否则不得 Done。

---

## 3.5 安全与隐私

- [ ] 没有真实审计材料进入 Git；
- [ ] 没有 OCR 全文、Prompt 全文或模型完整复述进入 Git；
- [ ] 没有真实 API key、Token、院内 IP 或敏感拓扑进入 Git；
- [ ] `.env` 被忽略；
- [ ] 上传文件被忽略；
- [ ] 模型缓存、验收输出和中间图片被忽略；
- [ ] 日志不输出完整材料正文；
- [ ] API 不返回保存路径或完整敏感全文；
- [ ] 未经批准没有调用公网 LLM、OCR、Embedding 或遥测服务；
- [ ] 运行时联网或自动下载行为已明确说明；
- [ ] 文件上传、解析和临时文件处理符合当前安全要求；
- [ ] 错误响应不泄露内部服务细节。

任何 P0 安全问题存在时：

```text
自动 NO-GO
```

---

## 3.6 错误处理

- [ ] 用户输入错误返回可理解的 4xx；
- [ ] 外部或本地 Provider 故障返回受控错误；
- [ ] LLM 故障不伪装成正常审计结果；
- [ ] 单文件解析失败不导致混合请求全部失败，除非设计明确要求；
- [ ] 错误信息对用户安全、清晰；
- [ ] 内部日志能支持排查，但不泄露敏感内容；
- [ ] 超时、连接失败、非法响应等关键错误有测试；
- [ ] 没有未捕获异常导致无法解释的 500。

---

## 3.7 配置与依赖

- [ ] 新增依赖有明确理由；
- [ ] 依赖只在对应 Slice 引入；
- [ ] 没有提前加入未使用的大型依赖；
- [ ] 依赖版本和安装方式已记录；
- [ ] 本地配置通过 `.env` 或配置系统注入；
- [ ] `.env.example` 已同步；
- [ ] 默认配置不会意外访问公网；
- [ ] Mock、真实 Provider 和 Disabled 模式行为明确；
- [ ] 配置缺失时行为可预测；
- [ ] 未发生无法解释的环境漂移。

大型依赖、数据库、向量库和外部服务必须有 Project Owner 批准。

---

## 3.8 文档同步

- [ ] 当前 Slice 文档已更新；
- [ ] 行为变化已更新 API 或用户文档；
- [ ] 新配置已更新 `.env.example` 和部署文档；
- [ ] 新依赖已更新安装说明；
- [ ] 已知限制已记录；
- [ ] 测试和验收结果已记录；
- [ ] 当前状态已准备更新；
- [ ] 重要决策已写入 decision log；
- [ ] 新增治理文档存放在 `docs/governance/` 的正确子目录；
- [ ] 当前状态已更新到 `docs/governance/current_status.md`；
- [ ] 重要决策已更新到 `docs/governance/decision_log.md`；
- [ ] Slice 执行文档位于 `docs/governance/slices/`；
- [ ] 验收与 Gate Review 报告位于 `docs/governance/acceptance/`；
- [ ] 没有在 `docs/` 根目录散落新增治理文件；
- [ ] 所有移动后的旧路径引用已同步更新；
- [ ] 文档没有夸大当前能力。

文档不得声称：

```text
真实 Provider 已通过
完整 RAG 已完成
院内部署已验证
```

除非存在真实证据。

---

## 3.9 Git 与可回滚性

- [ ] `git status` 已检查；
- [ ] `git diff` 已检查；
- [ ] 无意外文件变化；
- [ ] 无敏感文件进入暂存区；
- [ ] 每个 Slice 变更可独立理解；
- [ ] 回滚路径明确；
- [ ] 建议 commit message 已提供；
- [ ] 重要节点 tag 建议已提供；
- [ ] 未经批准未执行 destructive Git 操作；
- [ ] 未经批准未 commit、tag、merge 或 push。

---

## 3.10 独立验证与批准

- [ ] Codex 已提交真实执行报告；
- [ ] Hermes 已独立验证；
- [ ] Hermes 未只依赖 Codex 口头总结；
- [ ] 所有必要命令已真实运行；
- [ ] 风险分级已确认；
- [ ] Gate Review 已完成（如适用）；
- [ ] Project Owner 已明确批准。

没有 Project Owner 批准：

```text
最多只能标记为 Verification Complete
不能标记 DONE
```

---

## 4. Slice 类型专项 Definition of Done

不同类型 Slice 还必须满足以下专项要求。

---

## 4.1 纯文档 Slice

适用于：

- README；
- 架构文档；
- 部署文档；
- 用户手册；
- 决策简报；
- 治理文件。

DoD：

- [ ] 文档目标明确；
- [ ] 内容与当前真实实现一致；
- [ ] 不包含真实敏感信息；
- [ ] 路径、命令和配置示例可理解；
- [ ] 不夸大未实现能力；
- [ ] 与其他正式文档无明显冲突；
- [ ] 重要规则已交叉引用；
- [ ] Project Owner 已确认。

纯文档 Slice 可以不写代码测试，但如文档包含命令，应尽可能验证命令准确性。

---

## 4.2 Bug 修复 Slice

DoD：

- [ ] Bug 已被可靠复现；
- [ ] 有失败回归测试；
- [ ] 根因已说明；
- [ ] 使用最小改动修复；
- [ ] 回归测试转为通过；
- [ ] 相关功能无新回归；
- [ ] 未顺手扩大范围；
- [ ] 风险和限制已记录。

---

## 4.3 文档解析 Slice

适用于：

- txt/md/csv；
- PDF；
- DOCX；
- XLSX；
- 图片；
- 扫描 PDF。

DoD：

- [ ] 正常样例解析通过；
- [ ] 空文件行为明确；
- [ ] 损坏文件受控失败；
- [ ] 不支持格式受控返回；
- [ ] 混合上传允许部分成功；
- [ ] 大文件限制明确；
- [ ] 返回状态准确；
- [ ] 页面、Sheet 或文档顺序保持；
- [ ] preview 与内部完整文本职责分离；
- [ ] 真实或合成验收样例已验证；
- [ ] 不泄露材料全文。

---

## 4.4 OCR Slice

DoD：

- [ ] Mock OCR 单元测试通过；
- [ ] OCR 成功、空文本、异常和 Disabled 路径均测试；
- [ ] 单个 OCR 失败不破坏其他文件；
- [ ] 至少一种真实 OCR Provider 完成验收，或明确 BLOCKED；
- [ ] 使用非敏感合成图片；
- [ ] 模型初始化和缓存路径已明确；
- [ ] 是否发生下载或联网已记录；
- [ ] 离线复用行为已验证或明确 BLOCKED；
- [ ] OCR Provider 生命周期符合设计；
- [ ] 识别耗时和已知限制已记录；
- [ ] 不将 OCR 全文或图片提交 Git。

若真实 Provider 未验收：

```text
不得声称 OCR 院内部署可用
```

---

## 4.5 Full Text Flow Slice

DoD：

- [ ] 后端内部保留完整解析文本；
- [ ] API 只暴露安全 preview；
- [ ] `audit_engine` 不再只使用 1000 字 preview；
- [ ] 模型输入遵守上下文预算；
- [ ] 预算按 token 或可验证的安全估算管理；
- [ ] 多文件分配策略明确；
- [ ] 截断行为明确；
- [ ] 截断提示由后端确定性生成；
- [ ] API 契约保持批准方案；
- [ ] 不无限制将全文塞给模型；
- [ ] 长文档、多文件和敏感数据测试通过；
- [ ] 所有对应 P1 `xfail` 转为正常通过。

---

## 4.6 LLM Client 与本地 Qwen Slice

DoD：

- [ ] `LLM_MODE` 显式区分 Mock 与真实模式；
- [ ] 本地无鉴权模式可工作；
- [ ] API key 为空时不强制发送 Authorization；
- [ ] 真实模型 ID 已通过 `/v1/models` 验证；
- [ ] 模型地址、名称和 timeout 来自配置；
- [ ] timeout、连接失败、HTTP 错误、非法 JSON、缺少 choices 均受控；
- [ ] LLM 错误不伪装成正常审核结果；
- [ ] 前端能展示安全错误提示；
- [ ] 普通 CI 使用 Mock；
- [ ] 本地 Qwen 真实验收单独执行；
- [ ] 真实 Qwen 验收记录响应、耗时和限制；
- [ ] 未泄露 endpoint、材料正文和密钥。

若真实本地 Qwen 未验收：

```text
不得声称真实 LLM 链路完成
```

---

## 4.7 上传护栏与临时文件清理 Slice

DoD：

- [ ] 最大文件数量可配置；
- [ ] 最大单文件大小可配置；
- [ ] 最大总上传大小可配置；
- [ ] PDF 最大页数限制明确；
- [ ] 图片最大尺寸或像素限制明确；
- [ ] 超限返回安全、明确的 4xx；
- [ ] 路径穿越受到防护；
- [ ] 同名文件不会覆盖；
- [ ] 请求结束后临时文件按批准策略清理；
- [ ] 清理失败有日志但不泄露敏感内容；
- [ ] 混合上传行为明确；
- [ ] 安全与资源限制测试通过。

---

## 4.8 Embedding Client Slice

DoD：

- [ ] Provider 接口稳定；
- [ ] 普通测试使用 fake embedding；
- [ ] 输入 N 条文本返回 N 个向量；
- [ ] 空输入行为明确；
- [ ] 批量行为明确；
- [ ] timeout 和错误行为受控；
- [ ] 真实院内 Embedding endpoint 单独验收；
- [ ] 真实向量维度已验证；
- [ ] 模型名称、维度和 Provider 来自配置；
- [ ] 未将真实 Provider 纳入默认 CI；
- [ ] 未把生成式 Qwen 模型错误当作 Embedding 模型。

---

## 4.9 Regulation Indexer / ChromaDB Slice

DoD：

- [ ] 只索引批准目录；
- [ ] 支持文件扫描与解析；
- [ ] Chunk 策略有版本号；
- [ ] Chunk ID 稳定且唯一；
- [ ] Metadata 至少包含来源文件和索引版本；
- [ ] Collection 记录：
  - embedding model；
  - embedding dimension；
  - distance metric；
  - chunk strategy version；
  - index schema version；
- [ ] 上述关键参数变化时强制重建索引；
- [ ] 空文档和不支持文件受控处理；
- [ ] 普通 CI 使用 fake embedding；
- [ ] 临时 Chroma 集成测试通过；
- [ ] 真实院内 Embedding 验收独立完成；
- [ ] 未提前锁死最终 `audit_engine` 集成；
- [ ] 未宣称正式 RAG 已完成。

---

## 4.10 Vector Retriever Slice

DoD：

- [ ] Query 接口稳定；
- [ ] `top_k` 行为明确；
- [ ] 空索引返回受控空结果；
- [ ] 返回 Chunk 与 metadata 符合 schema；
- [ ] 相似度或距离语义明确；
- [ ] Retriever 不调用 LLM；
- [ ] 测试使用可控合成数据；
- [ ] 真实检索验收记录模型、维度、距离度量和索引版本；
- [ ] 未把 preview 当全文；
- [ ] 未提前宣称完整分析链路完成。

---

## 4.11 最终 RAG 集成 Slice

DoD：

- [ ] Full Text Flow Gate 已通过；
- [ ] 本地 Qwen Gate 已通过；
- [ ] 至少一种真实 OCR Provider Gate 已通过；
- [ ] 上传护栏与清理 Gate 已通过；
- [ ] Embedding、Indexer 和 Retriever 已分别通过 DoD；
- [ ] `audit_engine` 是唯一最终编排者；
- [ ] 上传材料和制度检索片段的 token budget 明确；
- [ ] 不把 preview 当完整材料；
- [ ] 制度片段来源对用户可见；
- [ ] Prompt 明确制度可能包含历史文件；
- [ ] LLM 错误受控；
- [ ] 真实端到端非敏感样例通过；
- [ ] 性能和已知限制已记录；
- [ ] 没有 P0；
- [ ] 所有 RAG 硬门槛 P1 已解决；
- [ ] 完成统一 Gate Review；
- [ ] Project Owner 批准。

---

## 4.12 部署 Slice

DoD：

- [ ] 目标机器环境已记录；
- [ ] 启动步骤可重复；
- [ ] `.env` 配置已验证；
- [ ] 本地 Qwen 可访问；
- [ ] OCR 模型已预置或明确禁用；
- [ ] 无运行时未授权公网访问；
- [ ] 上传和日志目录权限合理；
- [ ] 重启后可恢复；
- [ ] 离线启动已验证或明确 BLOCKED；
- [ ] 数据残留策略明确；
- [ ] 回滚步骤明确；
- [ ] 真实材料不进入 Git；
- [ ] 已知限制和操作说明完整；
- [ ] Project Owner 批准部署。

---

## 5. Gate Review Definition of Done

关键阶段通过 Gate Review，需要：

- [ ] Gate 范围明确；
- [ ] 所有硬门槛均有证据；
- [ ] 测试基线可信；
- [ ] 无无法解释的失败；
- [ ] P0 为零；
- [ ] 所有阻塞性 P1 已解决或被 Project Owner 明确接受；
- [ ] 真实 Provider 已按要求验收；
- [ ] 性能和安全风险已记录；
- [ ] 回滚方案存在；
- [ ] 当前状态和决策文档同步；
- [ ] Hermes 给出独立监督结论；
- [ ] Project Owner 给出 `GO`、`CONDITIONAL GO` 或 `NO-GO`。

只有 `GO` 或 Project Owner 明确批准的 `CONDITIONAL GO`，才能进入下一关键阶段。

---

## 6. 当前 AuditPilot 的关键硬门槛

以下问题在最终 RAG 集成前属于硬门槛：

- [ ] Full Text Flow 已完成；
- [ ] 不再只把 preview 发送给 LLM；
- [ ] 长文档截断明确；
- [ ] Token budget 策略明确；
- [ ] LLM 错误不伪装成正常结果；
- [ ] 本地 Qwen 真实验收通过；
- [ ] 上传文件数量、大小和资源限制完成；
- [ ] 临时上传文件清理策略完成；
- [ ] 至少一种真实 OCR Provider 验收通过；
- [ ] Embedding 模型和维度真实验证；
- [ ] Slice 3 基础设施测试通过；
- [ ] 最终 `audit_engine` 集成经过统一 Gate Review。

混合 PDF 逐页 OCR 是否为 Demo 硬门槛，由 Project Owner 根据真实材料构成决定。

---

## 7. 不允许作为 Done 证据的内容

以下内容单独存在时，不足以证明 Done：

```text
Codex 说“已完成”
Hermes 说“看起来没问题”
测试数量增加
CI 图标绿色
页面可以打开
Mock Provider 通过
编译通过
单个 happy path 通过
文档写了“已支持”
代码文件存在
Tag 名称看起来像完成
```

必须同时检查实际范围、测试、风险、真实 Provider、文档和 Owner 批准。

---

## 8. 完成报告模板

每个 Slice 提交验收时，使用以下模板：

```markdown
# Slice Completion Report

## 基本信息

- Slice：
- Commit：
- Tag：
- 执行者：
- 监督者：
- 日期：

## 目标与范围

- Goal：
- Non-goals：
- 实际完成：
- 未完成：

## 变更

- 修改文件：
- 新增文件：
- 删除文件：
- 新增依赖：
- API 契约变化：
- 架构变化：

## TDD 证据

- Red 阶段测试：
- 失败原因：
- Green 阶段实现：
- Refactor：
- 回归测试：

## 验证结果

- compileall：
- pytest：
- ruff：
- frontend build：
- CI：
- CodeQL：
- local provider：
- manual acceptance：

## 风险

- P0：
- P1：
- P2：
- P3：
- 已知限制：

## 安全与隐私

- 外部连接：
- 敏感数据检查：
- Git ignore 检查：
- 日志检查：

## DoD 检查

- 通用 DoD：
- 专项 DoD：
- 未满足项：

## 结论

- 建议状态：DONE / CONDITIONAL_DONE / PARTIAL / BLOCKED / FAILED
- Hermes 建议：
- Project Owner 决策：
```

---

## 9. Project Owner 快速验收问题

Project Owner 在批准前，至少确认：

1. 这次究竟实现了什么？
2. 有没有实现不该实现的东西？
3. 哪些测试先失败、后来通过？
4. 有没有新的普通测试失败或 `xfail`？
5. 有没有修改 API、架构或依赖？
6. 有没有敏感数据或外部连接风险？
7. 真实 Provider 是否真的验证过？
8. 当前结果是否可回滚？
9. 还有哪些 P0/P1？
10. 是否满足本文件适用的 DoD？

任一答案不清楚时，可以要求补充，不必批准 Done。

---

## 10. 最终 Definition of Done

AuditPilot 中的“完成”意味着：

```text
目标完成
且范围未越界
且测试先行并通过
且架构边界保持
且错误可控
且敏感数据安全
且真实环境得到必要验证
且文档同步
且变更可回滚
且证据可复现
且 Project Owner 明确批准
```

在此之前，只能称为：

```text
实现中
已验证
有条件可用
或等待批准
```

不能称为完成。
