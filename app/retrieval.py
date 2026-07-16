from typing import List

from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from qdrant_client import QdrantClient

from app.config import settings


def get_embedding_model():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def retrieve_chunks(question: str, top_k: int = 5) -> List[Document]:
    embedding_model = get_embedding_model()

    client = QdrantClient(url=settings.qdrant_url)
    vector_store = QdrantVectorStore(
        client=client,
        embedding=embedding_model,
        collection_name=settings.qdrant_collection
    )

    retriever = vector_store.as_retriever(search_kwargs={"k": top_k})
    docs = retriever.invoke(question)

    return docs


def format_sources(documents: List[Document]) -> List[str]:
    sources = []
    for doc in documents:
        source = doc.metadata.get("source", "Unknown")
        if source not in sources:
            sources.append(source)
    return sources