import base64
import hashlib
import json
import os
import re
import tempfile
from urllib.parse import urlparse
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import chromadb
from chromadb.config import Settings
from fastapi import FastAPI, HTTPException
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings

app = FastAPI()

DEFAULT_SYSTEM_PROMPT = (
    "You are a quiz generator. You must return ONLY valid JSON. "
    "Do not include markdown or any extra text."
)

STRICT_JSON_PROMPT = """\
You are a quiz generator.

You MUST return ONLY a valid JSON array.
DO NOT include markdown, explanations, or extra text.
DO NOT wrap the JSON in backticks.
DO NOT include newlines before or after the JSON.

Each element MUST have exactly this structure:
{{
  "id": number,
  "question": string,
  "options": [string, string, string, string],
  "correctIndex": number
}}

Rules:
- Generate exactly {n} questions.
- Each question must have exactly 4 options.
- correctIndex must be 0, 1, 2, or 3.
- Questions MUST come from the provided context.
- Do NOT invent new questions.
- IDs must be sequential starting at 1.

Context:
----------------
{context}
----------------
"""


class NIMEmbedding(Embeddings):
    def __init__(self, endpoint: str, token: str, model: str, max_chars: int = 2000):
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.model = model
        self.max_chars = max_chars

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text).strip()
        if len(text) > self.max_chars:
            text = text[: self.max_chars]
        if not text:
            raise ValueError("Empty text after cleaning")
        return text

    def _embed(self, text: str, input_type: str) -> list[float]:
        text = self._clean_text(text)
        resp = requests.post(
            f"{self.endpoint}/embeddings",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": text,
                "input_type": input_type,
            },
            timeout=60,
            verify=False,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Embedding error {resp.status_code}: {resp.text}")
        return resp.json()["data"][0]["embedding"]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for t in texts:
            try:
                vectors.append(self._embed(t, input_type="passage"))
            except Exception:
                continue
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text, input_type="query")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_pdf_bytes(pdf_url: Optional[str], pdf_path: Optional[str]) -> bytes:
    if pdf_url:
        resp = requests.get(pdf_url, timeout=60, verify=False)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to download PDF: {resp.text}")
        return resp.content
    if pdf_path:
        path = Path(pdf_path)
        if not path.exists():
            raise HTTPException(status_code=400, detail="pdf_path does not exist")
        return path.read_bytes()
    raise HTTPException(status_code=400, detail="Upload PDF(s) or provide pdf_url")


def _load_pdfs_from_payload(pdfs: list[dict[str, str]]) -> list[bytes]:
    blobs = []
    for item in pdfs:
        b64 = item.get("content_b64", "")
        if not b64:
            continue
        blobs.append(base64.b64decode(b64))
    return blobs


def _build_vectorstore(
    pdf_bytes_list: list[bytes],
    embeddings: Embeddings,
    persist_root: Path,
    chunk_size: int,
    chunk_overlap: int,
) -> Chroma:
    combined = b"".join(pdf_bytes_list)
    doc_hash = _sha256_bytes(combined)
    collection_name = f"pdf-{doc_hash[:8]}"

    chroma_url = os.getenv("RAG_CHROMA_URL", "").strip()
    if chroma_url:
        parsed = urlparse(chroma_url)
        host = parsed.hostname or chroma_url
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        ssl = parsed.scheme == "https"
        ssl_verify = os.getenv("RAG_CHROMA_SSL_VERIFY", "true").lower() != "false"
        settings = Settings(chroma_server_ssl_verify=ssl_verify)
        client = chromadb.HttpClient(
            host=host,
            port=port,
            ssl=ssl,
            settings=settings,
        )
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            client=client,
        )
    else:
        persist_dir = persist_root / doc_hash
        persist_dir.mkdir(parents=True, exist_ok=True)
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(persist_dir),
        )

    if vectorstore._collection.count() > 0:
        return vectorstore

    documents = []
    for pdf_bytes in pdf_bytes_list:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
        loader = PyPDFLoader(tmp_path)
        documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(documents)

    # Explicitly compute embeddings to avoid server-side embedding requirements.
    texts: list[str] = []
    metadatas: list[dict] = []
    vectors: list[list[float]] = []
    for doc in chunks:
        try:
            embedded = embeddings.embed_documents([doc.page_content])
        except Exception:
            continue
        if not embedded:
            continue
        texts.append(doc.page_content)
        metadatas.append(doc.metadata or {})
        vectors.append(embedded[0])

    if texts:
        vectorstore.add_texts(texts, metadatas=metadatas, embeddings=vectors)

    return vectorstore


def _extract_num_questions(user_prompt: str, default_n: int = 5) -> int:
    match = re.search(r"\b(\d+)\b", user_prompt or "")
    if not match:
        return default_n
    return int(match.group(1))


def _normalize_llm_endpoint(endpoint: str) -> str:
    endpoint = (endpoint or "").rstrip("/")
    if endpoint.endswith("/chat/completions"):
        return endpoint
    if endpoint.endswith("/v1"):
        return f"{endpoint}/chat/completions"
    return f"{endpoint}/v1/chat/completions"


def _call_llm(endpoint: str, token: str, model: str, system_prompt: str, user_prompt: str) -> str:
    if not endpoint:
        raise HTTPException(status_code=400, detail="llm.endpoint is required")
    endpoint = _normalize_llm_endpoint(endpoint)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = {
        "model": model or "default",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    resp = requests.post(endpoint, headers=headers, json=body, timeout=120, verify=False)
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"LLM error {resp.status_code}: {resp.text}")
    data = resp.json()
    return data.get("choices", [{}])[0].get("message", {}).get("content", "")


@app.post("/chat/completions")
async def chat_completions(payload: Dict[str, Any]):
    rag = payload.get("rag", {}) or {}
    messages = payload.get("messages", [])

    user_msg = next((m.get("content") for m in messages if m.get("role") == "user"), "") or ""
    system_msg = next((m.get("content") for m in messages if m.get("role") == "system"), "") or ""
    system_msg = system_msg or DEFAULT_SYSTEM_PROMPT

    n_questions = _extract_num_questions(user_msg, default_n=5)

    pdf_url = rag.get("pdf_url") or os.getenv("RAG_PDF_URL", "")
    pdf_path = rag.get("pdf_path") or os.getenv("RAG_PDF_PATH", "")
    pdfs_payload = rag.get("pdfs", []) or []

    embedding = rag.get("embedding", {}) or {}
    llm = rag.get("llm", {}) or {}

    embedding_endpoint = embedding.get("endpoint") or os.getenv("RAG_EMBEDDING_ENDPOINT", "")
    embedding_token = embedding.get("token") or os.getenv("RAG_EMBEDDING_TOKEN", "")
    embedding_model = embedding.get("model") or os.getenv("RAG_EMBEDDING_MODEL", "")

    llm_endpoint = llm.get("endpoint") or os.getenv("RAG_LLM_ENDPOINT", "")
    llm_token = llm.get("token") or os.getenv("RAG_LLM_TOKEN", "")
    llm_model = llm.get("model") or os.getenv("RAG_LLM_MODEL", "default")

    chunk_size = int(rag.get("chunk_size") or os.getenv("RAG_CHUNK_SIZE", "512"))
    chunk_overlap = int(rag.get("chunk_overlap") or os.getenv("RAG_CHUNK_OVERLAP", "64"))
    top_k = int(rag.get("top_k") or os.getenv("RAG_TOP_K", "6"))

    if not embedding_endpoint or not embedding_model:
        raise HTTPException(status_code=400, detail="embedding.endpoint and embedding.model are required")

    pdf_bytes_list = _load_pdfs_from_payload(pdfs_payload)
    if not pdf_bytes_list:
        pdf_bytes_list = [_load_pdf_bytes(pdf_url, pdf_path)]
    embeddings = NIMEmbedding(embedding_endpoint, embedding_token, embedding_model)

    persist_root = Path(os.getenv("RAG_CHROMA_DIR", "/data/chroma"))
    vectorstore = _build_vectorstore(pdf_bytes_list, embeddings, persist_root, chunk_size, chunk_overlap)

    docs = vectorstore.similarity_search(user_msg or "quiz questions", k=top_k)
    context = "\n\n".join(d.page_content for d in docs)

    prompt = STRICT_JSON_PROMPT.format(n=n_questions, context=context)

    content = _call_llm(llm_endpoint, llm_token, llm_model, system_msg, prompt)
    match = re.search(r"\[[\s\S]*\]", content or "")
    if not match:
        raise HTTPException(status_code=500, detail="LLM did not return a JSON array")

    json_text = match.group(0)
    try:
        parsed = json.loads(json_text)
        if len(parsed) != n_questions:
            raise ValueError("Wrong number of questions")
        for q in parsed:
            if set(q.keys()) != {"id", "question", "options", "correctIndex"}:
                raise ValueError("Invalid question keys")
            if len(q["options"]) != 4:
                raise ValueError("Each question must have 4 options")
            if q["correctIndex"] not in [0, 1, 2, 3]:
                raise ValueError("correctIndex must be 0-3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"choices": [{"message": {"content": json_text}}]}


@app.get("/healthz")
def healthz():
    return {"ok": True}
