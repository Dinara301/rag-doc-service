from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient


@contextmanager
def client_for(app: FastAPI) -> Iterator[TestClient]:
    """Yield an httpx-based test client for `app` (Starlette's TestClient subclasses httpx.Client)."""
    with TestClient(app) as client:
        yield client
