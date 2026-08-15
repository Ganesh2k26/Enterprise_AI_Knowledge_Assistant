# Enterprise AI Knowledge Assistant (Atlas)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Chat with your documents.** A production-style, multi-tenant RAG platform that ingests PDFs, Office files, and images, retrieves relevant context with hybrid search, and streams grounded answers with citations — powered by local embeddings and Google Gemini.

**Repository:** [github.com/Ganesh2k26/Enterprise_AI_Knowledge_Assistant](https://github.com/Ganesh2k26/Enterprise_AI_Knowledge_Assistant)

---

## Highlights

- **Grounded answers** — Hybrid retrieval (semantic + lexical), citation verification, and confidence scoring
- **Multi-format ingestion** — PDF, DOCX, TXT, MD, CSV, XLSX, PPTX, PNG, JPEG with OCR fallback for scanned pages
- **Local embeddings** — [BAAI/bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5) via SentenceTransformers (no paid embedding API)
- **Streaming chat** — Server-Sent Events with regenerate, export, feedback, and suggested follow-ups
- **Enterprise-ready patterns** — JWT auth with refresh-token rotation, RBAC, rate limiting, repository/service layers, Alembic migrations
- **Runs locally in minutes** — SQLite + ChromaDB out of the box; MySQL + Redis supported for production

---

## Demo

| Dashboard | Chat | Documents |
|-----------|------|-----------|
| _Run locally and add screenshots here_ | _Streaming answers with citations_ | _Folder tree + OCR badges_ |

**Local URLs (dev):**

| Service | URL |
|---------|-----|
| Frontend | http://127.0.0.1:5173 |
| Backend API | http://127.0.0.1:8000 |
| Swagger docs | http://127.0.0.1:8000/docs |

---

## Architecture

```
┌─────────────────┐       ┌──────────────────────────────────┐       ┌─────────────┐
│   React SPA     │◄─────►│         FastAPI Backend           │◄─────►│  SQLite /   │
│ Vite · Redux    │  SSE  │ auth · documents · chat · admin │       │  MySQL 8    │
│ React Query     │       └───────────────┬──────────────────┘       └─────────────┘
└─────────────────┘                       │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
          ┌─────────▼────────┐  ┌─────────▼─────────┐  ┌───────▼───────┐
          │    ChromaDB       │  │ Local embeddings   │  │  Gemini API   │
          │  (per-org vectors)│  │ bge-small-en-v1.5  │  │ (chat only)   │
          └──────────────────┘  └────────────────────┘  └───────────────┘
                    ┌───────────────────────┐
                    │  Redis (optional)     │  rate limiting + token rotation
                    └───────────────────────┘
```

**Ingestion:** upload → validate → extract text (pdfplumber / python-docx / OCR) → parent/child chunking → embed → store in ChromaDB + metadata DB

**Retrieval:** embed query → over-fetch → hybrid re-rank → deduplicate → compress context → verify citations → stream from Gemini

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic v2 |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Redux Toolkit, TanStack Query |
| **AI / RAG** | ChromaDB, SentenceTransformers, Google Gemini, EasyOCR, pdfplumber |
| **Auth & Ops** | JWT + refresh rotation, Redis rate limiting, Prometheus metrics, structured JSON logs |
| **Deploy** | Docker Compose, GitHub Actions CI |

---

## Quick Start (Local)

### Prerequisites

- Python 3.12+
- Node.js 20+
- A free [Gemini API key](https://aistudio.google.com/apikey) (chat generation only)

### 1. Clone the repository

```bash
git clone https://github.com/Ganesh2k26/Enterprise_AI_Knowledge_Assistant.git
cd Enterprise_AI_Knowledge_Assistant
```

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set at minimum:

```env
SECRET_KEY=<generate-with-python-secrets-token_urlsafe-48>
GEMINI_API_KEY=<your-gemini-api-key>
DATABASE_URL=sqlite+aiosqlite:///./app.db
```

Start the API:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Tables and storage directories are created automatically on startup.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open **http://127.0.0.1:5173**, sign up, upload a document, and start chatting.

> Vite proxies `/api` to the backend in development — no extra CORS setup required.

---

## Docker Compose (Full Stack)

For MySQL + Redis + backend + frontend in containers:

```bash
cp backend/.env.example backend/.env
# Set SECRET_KEY and GEMINI_API_KEY in backend/.env

docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST routers (auth, documents, chat, admin, …)
│   │   ├── core/            # Config, security, logging
│   │   ├── database/        # Async engine, models base, init
│   │   ├── llm/             # Gemini provider (pluggable interface)
│   │   ├── middleware/      # Rate limiting, error handling
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── rag/             # Loaders, chunking, embeddings, retrieval
│   │   ├── repositories/    # Data access layer
│   │   ├── schemas/         # Pydantic request/response models
│   │   └── services/        # Business logic
│   ├── alembic/             # Database migrations
│   ├── tests/               # Pytest suite
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/           # Login, Dashboard, Documents, Chat, Admin
│       ├── components/      # Layout, chat bubbles, auth guard
│       ├── hooks/           # useAuth, useChatStream (SSE)
│       ├── services/        # Axios client + API modules
│       └── store/           # Redux (auth, theme)
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## Environment Variables

See [`backend/.env.example`](backend/.env.example) for the full list.

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing secret | _(required)_ |
| `GEMINI_API_KEY` | Google Gemini API key | _(required for chat)_ |
| `DATABASE_URL` | Async SQLAlchemy URL | `sqlite+aiosqlite:///./app.db` |
| `REDIS_URL` | Rate limit + token rotation | `redis://localhost:6379/0` |
| `EMBEDDING_MODEL` | Local embedding model | `BAAI/bge-small-en-v1.5` |
| `CHROMA_PERSIST_DIR` | Vector store path | `./chroma_data` |
| `OCR_ENABLED` | EasyOCR for scanned PDFs | `true` |

Generate a secure secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## API Overview

Interactive docs: **http://localhost:8000/docs**

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/register` | Create organization + owner account |
| `POST /api/v1/auth/login` | Issue access + refresh tokens |
| `POST /api/v1/documents/upload` | Upload and ingest a document |
| `POST /api/v1/chat/messages` | Stream a RAG answer (SSE) |
| `GET /api/v1/admin/overview` | Usage statistics (admin) |

---

## Testing

```bash
cd backend
pytest -v
```

Tests use in-memory SQLite. Refresh-token rotation tests benefit from a local Redis instance; CI runs Redis automatically via GitHub Actions.

```bash
cd frontend
npm run build    # Type-check + production build
npm run lint
```

---

## Deployment Notes

| Component | Suggested platform |
|-----------|-------------------|
| Database | Railway, Aiven (MySQL) |
| Redis | Upstash (free tier) |
| Backend | Render, Railway (Docker) |
| Frontend | Vercel, Netlify |
| Vector store | Persistent volume on backend host (`CHROMA_PERSIST_DIR`) |

Set `ENVIRONMENT=production`, use a strong `SECRET_KEY`, and point `DATABASE_URL` at MySQL for production workloads.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `GEMINI_API_KEY is not set` | Add key to `backend/.env` and restart backend |
| First upload is slow | Embedding + OCR models download on first use (~130 MB) |
| Port 8000 already in use | Stop other uvicorn processes or change the port |
| Refresh token 401 after tab switch | Expected — tokens are single-use and rotate on refresh |
| OCR returns empty text | Ensure network access for EasyOCR model download, or disable `OCR_ENABLED` |

---

## Roadmap

| Implemented | Planned / out of scope |
|-------------|------------------------|
| JWT auth, RBAC, password strength | OAuth (Google / GitHub) |
| Hybrid RAG + citations | Cross-encoder re-ranking |
| Local embeddings + Gemini chat | Additional LLM providers |
| Admin dashboard + Prometheus | OpenTelemetry tracing |
| Docker + CI | Celery background ingestion workers |

The codebase is structured for extension — e.g. add a new LLM by implementing `LLMProvider` in `app/llm/` and registering it in `factory.py`.

---

## Author

**Ganesh** — [GitHub @Ganesh2k26](https://github.com/Ganesh2k26)

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Screenshorts And Results
<img width="1913" height="898" alt="Screenshot 2026-08-15 180730" src="https://github.com/user-attachments/assets/e4274947-90a8-416f-9937-077ea28151fc" />
<img width="1916" height="900" alt="Screenshot 2026-08-15 180747" src="https://github.com/user-attachments/assets/e9f34e28-100f-46ca-ad76-729000d83ccc" />
<img width="1910" height="904" alt="Screenshot 2026-08-15 180808" src="https://github.com/user-attachments/assets/fbff5190-ca09-4b71-8a08-c345942fe555" />
<img width="1909" height="899" alt="Screenshot 2026-08-15 180824" src="https://github.com/user-attachments/assets/4b91904f-1ecb-45c5-87e0-934ecdd72d3a" />




