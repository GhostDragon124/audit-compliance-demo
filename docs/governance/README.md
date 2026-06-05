# AuditPilot Governance Control Plane

`docs/governance/` is the governance control plane for AuditPilot.

It stores project governance rules, current status, accepted decisions, Slice documents, and acceptance evidence. Chat records are not an official source of truth.

## Files and Directories

| Path | Responsibility |
|---|---|
| `docs/governance/README.md` | Entry point for governance documents and reading order |
| `docs/governance/governance.md` | Governance roles, decision rules, Slice lifecycle, risk and change control |
| `docs/governance/definition_of_done.md` | Definition of Done and verification gates |
| `docs/governance/current_status.md` | Current factual project state, active Slice, blockers and next gate |
| `docs/governance/decision_log.md` | Accepted project decisions and their consequences |
| `docs/governance/slices/` | Approved or proposed Slice documents |
| `docs/governance/acceptance/` | Slice acceptance, Gate Review, real Provider validation, deployment acceptance and performance baseline evidence |

## Agent Reading Order

Agents must read governance sources in this order before starting a task:

1. `AGENTS.md`
2. `docs/architecture.md`
3. `docs/governance/README.md`
4. `docs/governance/governance.md`
5. `docs/governance/definition_of_done.md`
6. `docs/governance/current_status.md`
7. `docs/governance/decision_log.md`
8. The current Slice file specified by `docs/governance/current_status.md`

## Static and Dynamic Documents

Static governance rules change infrequently:

- `docs/governance/governance.md`
- `docs/governance/definition_of_done.md`

Dynamic project state changes as work progresses:

- `docs/governance/current_status.md`
- `docs/governance/decision_log.md`
- `docs/governance/slices/`
- `docs/governance/acceptance/`

Current status, decisions, Slice plans, and acceptance evidence must be stored under `docs/governance/`. Agents must not create new governance files directly in the `docs/` root.
