# RAG Knowledge Base

A Retrieval-Augmented Generation (RAG) system for k3s documentation Q&A.

## Overview

This project provides:
- **REST API** for querying k3s documentation
- **Web UI** for chatting with either the docs Q&A or the cluster-troubleshooting agent
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

`k8s/` is a Helm chart — [k8s/values.yaml](k8s/values.yaml) is the single place that drives every environment-specific value (docs path, image, Groq model, resource limits, etc.), so deploying on a different machine only means overriding a few `--set` flags, not editing YAML across multiple files.

### 1. Create the namespace

```bash
kubectl create namespace rag-system
```

### 2. Deploy Qdrant

```bash
helm repo add qdrant https://qdrant.github.io/qdrant-helm
helm install qdrant qdrant/qdrant -n rag-system -f k8s/qdrant-values.yaml
```

### 3. Deploy the app

```bash
helm install rag-app ./k8s -n rag-system \
  --set groqApiKey=<your-groq-api-key> \
  --set docsHostPath=/path/to/your/docs \
  --set image.repository=<your-dockerhub-username>/rag-knowledge-base
```

`docsHostPath` is the value most people need to change — it's a `hostPath` mount, so it must point to a real directory on the Kubernetes **node's** filesystem (not your laptop, unless that's also the node). `image.repository` should match whatever your [CI/CD](#cicd) workflow publishes to. See [k8s/values.yaml](k8s/values.yaml) for the full list of configurable values.

To apply changes later (new image, new docs path, etc.):
```bash
helm upgrade rag-app ./k8s -n rag-system --set ...
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

## CI/CD

[.github/workflows/docker-publish.yml](.github/workflows/docker-publish.yml) builds the Docker image and pushes it to Docker Hub as `<dockerhub-username>/rag-knowledge-base:latest` and `:<short-sha>` on every push to `main`, or on demand via the "Run workflow" button in the Actions tab.

Requires two repo secrets (**Settings → Secrets and variables → Actions**):

| Secret | Value |
|--------|-------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | A Docker Hub access token (Account Settings → Security → New Access Token) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Chat UI (docs Q&A + cluster agent) |
| GET | `/health` | Health check |
| POST | `/ingest` | Re-ingest documents |
| POST | `/query` | Ask a question about the k3s docs |
| POST | `/cluster/query` | Ask about live cluster state, e.g. "why is rag-app down?" |

Open `http://<node-ip>:30080/` (or `http://localhost:8000/` locally) for a simple chat interface — a mode toggle switches between the two endpoints above.

`/cluster/query` takes `{"question": "..."}` and returns `{"answer": "...", "tools_used": [...]}`. It's backed by a tool-calling agent ([app/cluster_agent.py](app/cluster_agent.py)) with read-only Kubernetes access ([app/cluster_tools.py](app/cluster_tools.py)) — it can list pods, describe a pod's status/events, and read pod logs, but has no permission to create, modify, or delete anything (enforced both by the tools themselves and by the ClusterRole in [k8s/templates/rbac.yaml](k8s/templates/rbac.yaml), scoped cluster-wide but strictly to `get`/`list`/`watch`).

```bash
curl -X POST http://<node-ip>:30080/cluster/query \
  -H "Content-Type: application/json" \
  -d '{"question": "why is the rag-app pod not starting?"}'
```

## Project Structure

```
rag-knowledge-base/
├── app/
│   ├── __init__.py
│   ├── config.py        # Settings management
│   ├── ingestion.py     # Document loading and indexing
│   ├── retrieval.py     # Vector search
│   ├── query.py         # RAG query chain
│   ├── cluster_tools.py # Read-only Kubernetes tools (list/describe pods, logs)
│   ├── cluster_agent.py # Tool-calling agent for /cluster/query
│   ├── models.py        # Pydantic models
│   ├── main.py          # FastAPI server
│   ├── cli.py           # CLI chatbot
│   └── static/
│       └── index.html   # Web chat UI
├── k8s/                  # Helm chart for the app
│   ├── Chart.yaml
│   ├── values.yaml       # single place to override docs path, image, resources, etc.
│   ├── qdrant-values.yaml  # values for the separate Qdrant chart
│   └── templates/
│       ├── configmap.yaml
│       ├── secret.yaml
│       ├── rbac.yaml       # ServiceAccount + read-only ClusterRole for cluster_tools.py
│       ├── deployment.yaml
│       └── service.yaml
├── .github/
│   └── workflows/
│       └── docker-publish.yml
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
| `DOCS_PATH` | (see `.env.example`) | Docs source path — for Kubernetes this is set via the Helm chart's `docsHostPath` value instead, see [Kubernetes Deployment](#kubernetes-deployment) |
| `CHAT_MODEL` | llama-3.1-8b-instant | Groq chat model |

## Development

```bash
# Run tests
pytest tests/

# Run locally
uvicorn app.main:app --reload --port 8000
```