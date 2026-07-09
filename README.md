# RAG Knowledge Base

A Retrieval-Augmented Generation (RAG) system for k3s documentation Q&A.

## Overview

This project provides:
- **REST API** for querying k3s documentation
- **CLI chatbot** for interactive Q&A
- **Re-ingest capability** to update document index

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Your k3s  │────>│  Ingestion  │────>│   Qdrant    │
│   docs      │     │   Pipeline │     │  Vector DB  │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              v
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────>│   FastAPI   │────>│  RAG Chain  │
│   Query     │     │   Server    │     │ (retrieve   │
└─────────────┘     └─────────────┘     │  + generate)│
                                         └─────────────┘
                                              │
                                              v
                                         ┌─────────────┐
                                         │    Groq     │
                                         │    LLM      │
                                         └─────────────┘
```

## Stack

- **LLM**: Groq (llama-3.1-8b-instant)
- **Embeddings**: HuggingFace (all-MiniLM-L6-v2)
- **Vector DB**: Qdrant
- **Framework**: LangChain + FastAPI

## Quick Start


### 1. Create a clean virtual environment

```bash
cd projects/rag-knowledge-base
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and set your GROQ_API_KEY and other variables
```

### 4. Start Qdrant (local or Docker)

```bash
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 5. Start the API server

```bash
uvicorn app.main:app --reload --port 8000
```

### 6. Ingest documents

```bash
curl -X POST http://localhost:8000/ingest
```

### 7. Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I troubleshoot high CPU on a node?"}'
```

### 8. CLI chatbot

```bash
# Single query
python -m app.cli "How do I restart a deployment?"

# Interactive mode
python -m app.cli -i
```

## Kubernetes Deployment

### 1. Add Helm repo and deploy Qdrant

```bash
helm repo add qdrant https://qdrant.github.io/qdrant-helm
helm install qdrant qdrant/qdrant -n rag-system -f k8s/qdrant-values.yaml
```

### 2. Apply Kubernetes manifests

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### 3. Update secret with your Groq API key

```bash
kubectl edit secret rag-app-secret -n rag-system
```

### 4. Ingest docs

```bash
kubectl exec -it -n rag-system deploy/rag-app -- python -m app.ingestion
```

### 5. Access the API

```bash
curl -X POST http://<node-ip>:30080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I list all pods?"}'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/ingest` | Re-ingest documents |
| POST | `/query` | Ask a question |

## Project Structure

```
rag-knowledge-base/
├── app/
│   ├── __init__.py
│   ├── config.py        # Settings management
│   ├── ingestion.py     # Document loading and indexing
│   ├── retrieval.py     # Vector search
│   ├── query.py         # RAG query chain
│   ├── models.py        # Pydantic models
│   ├── main.py          # FastAPI server
│   └── cli.py           # CLI chatbot
├── k8s/
│   ├── namespace.yaml
│   ├── qdrant-values.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment.yaml
│   └── service.yaml
├── tests/
│   └── test_rag.py
├── Dockerfile
├── requirements.txt
└── README.md
```

## Configuration

Environment variables (or `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | Required | Groq API key |
| `QDRANT_URL` | http://qdrant:6333 | Qdrant server URL |
| `QDRANT_COLLECTION` | k3s-docs | Collection name |
| `DOCS_PATH` | /home/sydney/Workstation/kubenetes/k3s | Docs source path |
| `CHAT_MODEL` | llama-3.1-8b-instant | Groq chat model |

## Development

```bash
# Run tests
pytest tests/

# Run locally
uvicorn app.main:app --reload --port 8000
```