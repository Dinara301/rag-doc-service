# Architecture Decision Records

An ADR is a short, dated record of one decision: what we faced, what we considered, what we chose, and what follows from it. They live next to the code so they are reviewed and versioned with it.

## When to write one

Write an ADR in the same change (or the commit just before it) whenever a choice has real alternatives: picking a library, a storage model, an error-handling policy, a rule change. Do not write one for routine code changes.

## Conventions

- File name: `NNNN-short-title.md`, numbered in the order decisions are made. Numbers are never reused.
- Keep ADRs concise: aim for about 15 lines. One or two sentences per section, options as one-line bullets with the deciding trade-off, no repeated background. If it needs more, link to code or docs instead of pasting them.
- Status is one of: `Proposed`, `Accepted`, `Superseded by NNNN`, `Rejected`.
- Accepted ADRs are not rewritten. If a decision changes, add a new ADR and mark the old one `Superseded by NNNN`.
- Link the ADR from the commit body (`ADR: docs/adr/NNNN-...`) and mention it in `CHANGELOG.md` when the decision changes behavior.

## Template

Copy this into a new file:

```markdown
# NNNN. Title

- Status: Proposed | Accepted | Superseded by NNNN | Rejected
- Date: YYYY-MM-DD

## Context

One or two sentences: the problem or constraint, as facts.

## Options

- A: key pro / key con.
- B: key pro / key con.

## Decision

What we chose and the main reason, in a sentence or two.

## Consequences

Two or three bullets: what gets easier, harder, or must be watched.
```

## Index

- [0001. Adopt ADRs and a changelog](0001-adopt-adrs-and-changelog.md) - Accepted
- [0002. Relax dependency and infrastructure rules](0002-relax-dependency-and-infrastructure-rules.md) - Accepted
- [0003. Use uv, ruff, and pre-commit](0003-use-uv-ruff-and-pre-commit.md) - Accepted
- [0004. Config, lifespan, and health checks](0004-config-lifespan-and-health.md) - Accepted
- [0005. Observability stack](0005-observability-stack.md) - Accepted
- [0006. OpenAI error mapping and retries](0006-openai-error-mapping.md) - Accepted
- [0007. Ingest consistency](0007-ingest-consistency.md) - Accepted
- [0008. Token-aware chunking with a library](0008-token-aware-chunking-library.md) - Accepted
