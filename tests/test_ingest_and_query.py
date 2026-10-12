from pathlib import Path

from fastapi import FastAPI

from tests.conftest import AppFactory, FailingEmbedder
from tests.http import client_for

FIXTURE = Path(__file__).parent / "fixtures" / "widgets.md"
MARKDOWN = ("widgets.md", FIXTURE.read_bytes(), "text/markdown")


def test_ingest_and_query_returns_json_with_sources(app: FastAPI) -> None:
    with client_for(app) as client:
        ingest = client.post("/documents", files={"files": MARKDOWN})
        assert ingest.status_code == 200
        document = ingest.json()["documents"][0]
        assert document["filename"] == "widgets.md"
        assert document["chunk_count"] >= 1
        assert document["document_id"]

        listed = client.get("/documents")
        assert listed.status_code == 200
        assert listed.json()["documents"] == [document]

        query = client.post("/query", json={"question": "How do I create a widget?", "top_k": 3})
        assert query.status_code == 200
        body = query.json()
        assert body["answer"]
        source = body["sources"][0]
        assert source["document_id"] == document["document_id"]
        assert source["filename"] == "widgets.md"
        assert source["snippet"]
        assert 0.0 <= source["score"] <= 1.0


def test_multiple_files_in_one_request(app: FastAPI) -> None:
    files = [
        ("files", MARKDOWN),
        ("files", ("notes.txt", b"Restart the worker with `make restart`.", "text/plain")),
    ]
    with client_for(app) as client:
        response = client.post("/documents", files=files)
        assert response.status_code == 200
        names = [doc["filename"] for doc in response.json()["documents"]]
        assert names == ["widgets.md", "notes.txt"]
        assert len(client.get("/documents").json()["documents"]) == 2


def test_query_empty_corpus(app: FastAPI) -> None:
    with client_for(app) as client:
        response = client.post("/query", json={"question": "Anything here?"})
    assert response.status_code == 200
    body = response.json()
    assert body["sources"] == []
    assert "No documents" in body["answer"]


def test_query_validation_rejects_empty_question(app: FastAPI) -> None:
    with client_for(app) as client:
        response = client.post("/query", json={"question": ""})
    assert response.status_code == 422


def test_unsupported_file_type_returns_400(app: FastAPI) -> None:
    with client_for(app) as client:
        files = {"files": ("notes.docx", b"not supported", "application/octet-stream")}
        response = client.post("/documents", files=files)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_corrupt_pdf_returns_400(app: FastAPI) -> None:
    with client_for(app) as client:
        files = {"files": ("broken.pdf", b"definitely not a pdf", "application/pdf")}
        response = client.post("/documents", files=files)
    assert response.status_code == 400


def test_bad_file_in_batch_stores_nothing(app: FastAPI) -> None:
    files = [
        ("files", MARKDOWN),
        ("files", ("notes.docx", b"not supported", "application/octet-stream")),
    ]
    with client_for(app) as client:
        assert client.post("/documents", files=files).status_code == 400
        assert client.get("/documents").json()["documents"] == []


def test_delete_document(app: FastAPI) -> None:
    with client_for(app) as client:
        ingest = client.post("/documents", files={"files": MARKDOWN})
        document_id = ingest.json()["documents"][0]["document_id"]
        assert client.delete(f"/documents/{document_id}").status_code == 204
        assert client.delete(f"/documents/{document_id}").status_code == 404
        assert client.get("/documents").json()["documents"] == []


def test_missing_api_key_returns_503(make_app: AppFactory) -> None:
    app = make_app(api_key="")
    with client_for(app) as client:
        ingest = client.post("/documents", files={"files": MARKDOWN})
        query = client.post("/query", json={"question": "hello"})
        listed = client.get("/documents")
    assert ingest.status_code == 503
    assert query.status_code == 503
    assert listed.status_code == 200


def test_openai_failure_returns_502(make_app: AppFactory) -> None:
    app = make_app(embedder=FailingEmbedder())
    with client_for(app) as client:
        ingest = client.post("/documents", files={"files": MARKDOWN})
        query = client.post("/query", json={"question": "hello"})
    assert ingest.status_code == 502
    assert query.status_code == 502
    assert ingest.json() == {"detail": "OpenAI request failed"}
