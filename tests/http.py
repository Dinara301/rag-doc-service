from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient


@contextmanager
def client_for(app: FastAPI) -> Iterator[TestClient]:
    """httpx-based test client (Starlette's TestClient subclasses httpx.Client)."""
    with TestClient(app) as client:
        yield client
