import os
import hashlib
from pathlib import Path
from typing import List, Tuple

from langchain_groq import ChatGroq
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config import settings


def get_embedding_model():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)


def load_documents() -> List:
    docs_path = Path(settings.docs_path)
    if not docs_path.exists():
        raise FileNotFoundError(f"Documents path not found: {settings.docs_path}")

    loaders = {
        ".md": DirectoryLoader(
            str(docs_path),
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        ),
        ".txt": DirectoryLoader(
            str(docs_path),
            glob="**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        ),
        ".yml": DirectoryLoader(
            str(docs_path),
            glob="**/*.yml",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        ),
        ".yaml": DirectoryLoader(
            str(docs_path),
            glob="**/*.yaml",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        ),
    }

    documents = []
    for ext, loader in loaders.items():
        try:
            docs = loader.load()
            documents.extend(docs)
        except Exception as e:
            print(f"Error loading {ext} files: {e}")

    return documents


def chunk_documents(documents: List, chunk_size: int = 500, chunk_overlap: int = 50) -> List:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    return text_splitter.split_documents(documents)


def get_file_hash(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return hashlib.md5(f.read().encode()).hexdigest()


def create_collection_if_not_exists():
    client = get_qdrant_client()

    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if settings.qdrant_collection not in collection_names:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )
        print(f"Created collection: {settings.qdrant_collection}")
    else:
        print(f"Collection {settings.qdrant_collection} already exists")


def ingest_documents() -> Tuple[int, int]:
    print("Loading documents...")
    documents = load_documents()
    print(f"Loaded {len(documents)} documents")

    print("Chunking documents...")
    chunks = chunk_documents(documents, settings.chunk_size, settings.chunk_overlap)
    print(f"Created {len(chunks)} chunks")

    print("Creating Qdrant collection...")
    create_collection_if_not_exists()

    print("Embedding and storing in Qdrant...")
    embedding_model = get_embedding_model()

    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embedding_model,
        url=settings.qdrant_url,
        collection_name=settings.qdrant_collection,
        force_recreate=False
    )

    return len(chunks), len(documents)