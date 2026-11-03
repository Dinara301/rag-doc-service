# 0001. Adopt ADRs and a changelog

- Status: Accepted
- Date: 2026-11-03

## Context

The service is being hardened for production through ten planned phases, each made of small commits. Many of those commits involve real choices (libraries, storage model, error policy, rule changes). Commit messages alone bury the reasoning, and reviewers need to see both what changed and why, without reconstructing it from diffs.

## Options considered

1. Commit messages only: no extra files, but decisions are hard to find later and cannot be linked to or amended.
2. A wiki or external document: easy to read, but drifts from the code and is not reviewed with it.
3. Markdown files in the repository: ADRs for decisions and a CHANGELOG for user-visible changes. Reviewed in the same pull requests, versioned with the code, searchable offline.

## Decision

Use option 3.

- Decisions with real alternatives are recorded as ADRs in `docs/adr/`.
- Every change is listed in `CHANGELOG.md` under `[Unreleased]`, following the Keep a Changelog format (Added, Changed, Fixed, Removed).
- Commit bodies carry labelled lines (Why, What, Tests, Docs, ADR) so a single commit is understandable on its own.

## Consequences

- Each change takes a little more writing; in return, the reasoning stays with the code.
- Reviewers can read a pull request as a sequence of commits, each with its docs and ADR.
- ADRs are append-only: changing a decision means adding a new ADR that supersedes the old one.
