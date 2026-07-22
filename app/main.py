from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.models import QueryRequest, QueryResponse, IngestResponse, ClusterQueryRequest, ClusterQueryResponse
from app.query import query_rag
from app.ingestion import ingest_documents
from app.cluster_agent import query_cluster

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


@app.post("/cluster/query", response_model=ClusterQueryResponse)
async def cluster_query(request: ClusterQueryRequest):
    try:
        answer, tools_used = query_cluster(request.question)
        return ClusterQueryResponse(answer=answer, tools_used=tools_used)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cluster query failed: {str(e)}")


app.mount("/", StaticFiles(directory="app/static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)