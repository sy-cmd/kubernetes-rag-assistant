from pydantic import BaseModel
from typing import List, Optional


class DocumentChunk(BaseModel):
    content: str
    source: str
    chunk_index: int


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    chunks_used: int


class IngestResponse(BaseModel):
    status: str
    chunks_indexed: int
    documents_processed: int