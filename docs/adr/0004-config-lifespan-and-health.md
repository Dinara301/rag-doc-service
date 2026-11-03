# 0004. Config, lifespan, and health checks

- Status: Accepted
- Date: 2026-11-03

## Context

Settings were loaded by hand (`python-dotenv` plus `os.getenv`) with the API key as a plain string, and operators had only one shallow `/health`.

## Options

- Settings: `pydantic-settings` (typed, validated, `SecretStr`) / `dynaconf` (heavier, less typed) / keep hand-written (more code, key visible in `repr`).
- Health: separate live and ready endpoints / one deep `/health` (restarts an instance when a dependency blips).

## Decision

Use `pydantic-settings` `BaseSettings` with `SecretStr` for the API key. A missing key does not crash startup; readiness reports it. `/health/live` never checks dependencies (so a dependency blip does not restart the instance); `/health/ready` returns 503 with reasons when the key is missing or the store ping fails. `/health` stays as an alias of live.

## Consequences

- `python-dotenv` is no longer a direct dependency; env names match field names (`CHROMA_PATH`, `MAX_FILE_BYTES`, ...).
- Invalid values fail at startup with a clear validation error.
