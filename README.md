# AI Quiz Generator for HPE Private Cloud AI

AI Quiz Generator is a lightweight web UI that creates multiple‑choice quizzes from uploaded PDFs using a RAG pipeline.  
It is designed for deployment inside HPE Private Cloud AI via Helm charts, and can also run locally with Docker.

---

## Overview

The application provides:

- PDF upload (one or more files)
- RAG‑based question generation
- Multiple‑choice quiz UI with scoring
- Configurable embedding + LLM endpoints (OpenAI‑compatible)
- Production‑ready Docker images and Helm chart deployment

---

## Architecture

- Frontend: React + Vite + Tailwind
- Backend: Node/Express API
- RAG: FastAPI + LangChain + Chroma
- Optional external Chroma inside the cluster

---

## Deployment on HPE Private Cloud AI

This repo includes everything needed to deploy as a framework in HPE Private Cloud AI.

### Deployment steps

1. Open the AI Essentials interface.
1. Select "Import New Framework".
1. Upload the Helm chart file:
   `ai-quiz-generator-x.y.z.tgz`
1. Deploy the framework.
1. Set the runtime configuration in `values.yaml` (RAG endpoints and tokens).

Configuration is **not** entered in the UI.  
The UI only handles PDF uploads and quiz options.

---

## Configuration (values.yaml)

All runtime configuration is provided through the Helm chart values.

### Key fields

| Field | Description |
|---|---|
| `ragConfig.embeddingEndpoint` | Embedding API base URL (`/v1`) |
| `ragConfig.embeddingToken` | Embedding API token (optional) |
| `ragConfig.embeddingModel` | Embedding model name |
| `ragConfig.llmEndpoint` | LLM API base URL (`/v1`) |
| `ragConfig.llmToken` | LLM API token (optional) |
| `ragConfig.llmModel` | LLM model name |
| `ragConfig.chromaUrl` | External Chroma URL (recommended for persistence) |
| `ragConfig.chunkSize` | RAG chunk size |
| `ragConfig.chunkOverlap` | RAG chunk overlap |
| `ragConfig.topK` | Retrieval count |

Tokens are stored in a Kubernetes Secret created by the chart.

---

## Docker Usage (Optional)

```sh
docker run -d --name ai-quiz-frontend -p 3000:80 --restart unless-stopped vinchar/ai-quiz-generator-frontend:<tag>
docker run -d --name ai-quiz-backend -p 3001:3001 --restart unless-stopped vinchar/ai-quiz-generator-backend:<tag>
docker run -d --name ai-quiz-rag -p 8000:8000 --restart unless-stopped vinchar/ai-quiz-generator-rag:<tag>
```

---

## Repository Structure

| File/Folder | Description |
|---|---|
| `Dockerfile.frontend` | Frontend build + nginx runtime image |
| `Dockerfile.backend` | Node/Express backend |
| `Dockerfile.rag` | FastAPI RAG service |
| `ai-quiz-generator/` | Helm chart templates + values |
| `ai-quiz-generator-*.tgz` | Packaged Helm chart |
| `src/` | React frontend source |
| `server/` | Express backend |
| `rag/` | FastAPI RAG service |
| `k8s/` | Optional raw manifests |

---

## Troubleshooting

### 500 Internal Server Error on `/api/generate`

- Check RAG logs for Chroma connectivity or embedding errors.
- Verify `ragConfig.*` endpoints and tokens in `values.yaml`.

### Upload failures

- Ensure nginx proxy limits and timeouts are configured in the Helm chart.
- Verify Istio VirtualService timeout if using the provided template.
