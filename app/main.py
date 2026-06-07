from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.models import QueryRequest, QueryResponse, IngestResponse
from app.query import query_rag
from app.ingestion import ingest_documents

app = FastAPI(title="k3s RAG Knowledge Base", version="1.0.0")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rag-knowledge-base"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest():
    try:
        chunks_indexed, docs_processed = ingest_documents()
        return IngestResponse(
            status="success",
            chunks_indexed=chunks_indexed,
            documents_processed=docs_processed
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        answer, sources, chunks_used = query_rag(request.question, request.top_k)
        return QueryResponse(
            answer=answer,
            sources=sources,
            chunks_used=chunks_used
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)