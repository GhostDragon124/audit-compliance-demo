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
