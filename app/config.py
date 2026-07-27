from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    groq_api_key: str
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "k3s-docs"
    docs_path: str = "/home/sydney/Workstation/kubenetes/k3s"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    chat_model: str = "llama-3.1-8b-instant"
    minimax_api_key: str = ""
    minimax_base_url: str = "https://api.minimax.io/v1"
    cluster_chat_model: str = "MiniMax-M3"
    chunk_size: int = 500
    chunk_overlap: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()