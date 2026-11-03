# 0003. Use uv, ruff, and pre-commit

- Status: Accepted
- Date: 2026-11-03

## Context

Installs are unpinned (`>=` ranges, no lockfile), and there is no linter or formatter. Local and CI environments should match, and the docstring rule should be machine-checked.

## Options

- Dependencies: `uv` + `uv.lock` (fast, universal lockfile) vs pip-tools (extra step) vs poetry (heavier, own build backend).
- Lint/format: `ruff` (one tool for lint, format, imports, docstrings) vs flake8 + black + isort + pydocstyle (four tools).
- Gate: `pre-commit` hooks (same checks before every commit) vs CI only (late feedback).

## Decision

Adopt `uv` with a committed `uv.lock`, `ruff` (including pydocstyle rules), and `pre-commit`. They are introduced in separate steps of Plan 01.

## Consequences

- The lock is universal, so it must resolve for every platform in use. It requires Intel macOS (`required-environments`), where newer `onnxruntime` wheels are missing; the lock picks 1.23.2 there.
- `requires-python` is now `>=3.11,<3.15`: without an upper bound, resolution also targets Python 3.15, which has no Intel-macOS wheel for `onnxruntime`. Raise the cap when wheels exist.
- Dev tools move to `[dependency-groups]`; `pip install -e ".[dev]"` is replaced by `uv sync`.
