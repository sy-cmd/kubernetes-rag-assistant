import pytest
from app.query import query_rag
from app.ingestion import load_documents, chunk_documents
from app.config import settings


class TestConfig:
    def test_settings_loaded(self):
        assert settings.groq_api_key is not None
        assert settings.qdrant_url is not None
        assert settings.docs_path is not None


class TestIngestion:
    def test_load_documents(self):
        docs = load_documents()
        assert isinstance(docs, list)

    def test_chunk_documents(self):
        from langchain.schema import Document
        test_docs = [
            Document(page_content="This is a test document. " * 100, metadata={"source": "test.md"})
        ]
        chunks = chunk_documents(test_docs, chunk_size=100, chunk_overlap=10)
        assert len(chunks) > 0
        assert all(hasattr(chunk, "page_content") for chunk in chunks)


class TestQuery:
    def test_query_rag_returns_tuple(self):
        answer, sources, chunks_used = query_rag("How do I list pods in kubernetes?", top_k=2)
        assert isinstance(answer, str)
        assert isinstance(sources, list)
        assert isinstance(chunks_used, int)