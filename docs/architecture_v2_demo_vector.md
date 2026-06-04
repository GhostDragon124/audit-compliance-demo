# Audit Compliance Demo Architecture

## Scope

This project is an M0+ demo for an audit compliance analysis workflow. The current goal is to prove the end-to-end path:

Frontend file upload and audit question -> FastAPI backend -> basic file parsing -> mock or LLM response -> frontend result display.

## Current Modules

- `frontend/`: React + Vite + TypeScript single-page workspace.
- `backend/app/main.py`: FastAPI application, CORS, health check, and analyze API.
- `backend/app/services/document_parser.py`: Basic parser for `.txt`, `.md`, and `.csv`.
- `backend/app/services/audit_engine.py`: Business orchestration layer.
- `backend/app/services/llm_client.py`: OpenAI-compatible chat completions client with mock fallback.
- `backend/app/services/regulation_indexer.py`: Placeholder for future regulation indexing.
- `backend/app/services/vector_retriever.py`: Placeholder retriever that returns an empty list in M0+.
- `backend/app/services/embedding_client.py`: Placeholder for future embedding integration.

## Future Vector Flow

The intended later flow is:

1. Scan `data/regulations/raw/`.
2. Parse regulation documents.
3. Split documents into chunks.
4. Generate embeddings.
5. Store chunks and vectors in `data/indexes/chroma/regulations/`.
6. Retrieve relevant regulation chunks for each audit question.
7. Pass uploaded material, question, and retrieved chunks to the audit engine.

ChromaDB, embedding calls, and RAG are intentionally not implemented in M0+.
