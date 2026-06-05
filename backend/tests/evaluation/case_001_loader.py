"""
Case 001 Loader

Loads case data from the evaluation fixture directory.
Uses __file__ resolution (not cwd-dependent).
Prevents path traversal.
"""

from pathlib import Path
from typing import Dict, Any, List
import json
import yaml


def _get_project_root() -> Path:
    """Resolve project root by walking up from this file's location."""
    # This file is at backend/tests/evaluation/case_001_loader.py
    return Path(__file__).resolve().parents[3]


def get_case_root() -> Path:
    """Return the case 001 root directory path."""
    return (
        _get_project_root()
        / "data"
        / "tests"
        / "evaluation"
        / "case_001_procurement_pending_approval"
    )


def _safe_resolve(base: Path, relative_path: str) -> Path:
    """Resolve a path relative to base, preventing traversal outside base."""
    target = (base / relative_path).resolve()
    # Ensure the resolved path is under the base directory
    if not str(target).startswith(str(base.resolve())):
        raise ValueError(f"Path traversal detected: {relative_path}")
    return target


def _check_path_traversal(case_root: Path, path: str) -> Path:
    """Resolve path relative to case root and prevent traversal."""
    resolved = (case_root / path).resolve()
    if not str(resolved).startswith(str(case_root.resolve())):
        raise ValueError(f"Path traversal detected: {path}")
    return resolved


def load_manifest(case_root: Path | None = None) -> Dict[str, Any]:
    """Load and return the case manifest."""
    if case_root is None:
        case_root = get_case_root()
    manifest_path = case_root / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_question(case_root: Path | None = None) -> str:
    """Load and return the question text."""
    if case_root is None:
        case_root = get_case_root()
    question_path = case_root / "question.txt"
    return question_path.read_text(encoding="utf-8").strip()


def load_expected_results(case_root: Path | None = None) -> Dict[str, Any]:
    """Load and return the expected results YAML."""
    if case_root is None:
        case_root = get_case_root()
    results_path = case_root / "expected_results.yaml"
    with open(results_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_material_paths(case_root: Path | None = None) -> List[Path]:
    """Return safe resolved paths for all materials listed in manifest."""
    if case_root is None:
        case_root = get_case_root()
    manifest = load_manifest(case_root)
    paths = []
    for rel_path in manifest["materials"]:
        resolved = _check_path_traversal(case_root, rel_path)
        paths.append(resolved)
    return paths


def get_regulation_paths(case_root: Path | None = None) -> List[Path]:
    """Return safe resolved paths for all regulations listed in manifest."""
    if case_root is None:
        case_root = get_case_root()
    manifest = load_manifest(case_root)
    paths = []
    for rel_path in manifest["regulations"]:
        resolved = _check_path_traversal(case_root, rel_path)
        paths.append(resolved)
    return paths


def get_ground_truth_paths(case_root: Path | None = None) -> List[Path]:
    """Return safe resolved paths for all ground truth files listed in manifest."""
    if case_root is None:
        case_root = get_case_root()
    manifest = load_manifest(case_root)
    paths = []
    for rel_path in manifest["ground_truth"]:
        resolved = _check_path_traversal(case_root, rel_path)
        paths.append(resolved)
    return paths
