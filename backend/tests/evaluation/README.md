# Evaluation Tests

## Purpose

This directory contains evaluation harness tests for AuditPilot Case 001
(采购项目未完成审批且采购方式可能不符合规定).

The tests are organized as follows:

| File | Phase | Status |
|------|-------|--------|
| `test_case_001_fixture_validation.py` | Phase 0 | Fixture validation |
| `test_case_001_retrieval.py` | Slice 4A | Retrieval (xfail) |
| `test_case_001_prompt_grounding.py` | Slice 4B | Prompt grounding (xfail) |
| `test_case_001_end_to_end.py` | Slice 4C | End-to-end (xfail) |
| `case_001_loader.py` | Shared | Case 001 data loader |

## How to run

```bash
cd backend
.venv/bin/python -m pytest tests/evaluation/ -vv
```

Phase 0 tests must always pass (0 failed, 0 xfailed, 0 skipped).
Slices 4A/4B/4C are strict xfail until their respective implementations are done.
