# Architecture Decision Records

An ADR is a short, dated record of one decision: what we faced, what we considered, what we chose, and what follows from it. They live next to the code so they are reviewed and versioned with it.

## When to write one

Write an ADR in the same change (or the commit just before it) whenever a choice has real alternatives: picking a library, a storage model, an error-handling policy, a rule change. Do not write one for routine code changes.

## Conventions

- File name: `NNNN-short-title.md`, numbered in the order decisions are made. Numbers are never reused.
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

What problem or constraint forces a decision? Include facts, not opinions.

## Options considered

1. Option A: pros, cons.
2. Option B: pros, cons.

## Decision

What we chose and the main reason.

## Consequences

What becomes easier, what becomes harder, what we must do or watch as a result.
```

## Index

- [0001. Adopt ADRs and a changelog](0001-adopt-adrs-and-changelog.md) - Accepted
