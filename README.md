# 🧬 ScienceRAG

**AI-powered scientific literature intelligence platform**

Transform how you discover, synthesize, and understand academic research. Ask questions in natural language and get citation-backed answers synthesized from real scientific papers.

![ScienceRAG Demo](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

---

## ✨ Features

### 🔍 **Intelligent Paper Discovery**
- Natural language queries → relevant papers
- Searches **OpenAlex** (250M+ works) and **Semantic Scholar** (200M+ papers)
- Automatic deduplication across sources

### 🧠 **RAG-Powered Synthesis**
- Vector embeddings with OpenAI `text-embedding-3-small`
- Semantic search over chunked paper abstracts
- AI synthesis with inline citations

### 📊 **Real-Time Progress**
- Live sidebar showing ingestion progress
- Papers found, chunks created, embeddings generated
- Stage-by-stage pipeline visibility

### 🎨 **Modern Chat Interface**
- Floating pill input (ChatGPT-style)
- Citation tooltips on hover
- Expandable source cards
- Settings panel with data source toggles

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### 1. Clone the repository
```bash
git clone https://github.com/HiNala/bio_hack.git
cd bio_hack
```

### 2. Create your `.env` file
```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-key-here
```

### 3. Start all services
```bash
docker compose up --build -d
```

### 4. Open the app
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                       │
│  • Floating chat input                                       │
│  • Live progress sidebar                                     │
│  • Citation tooltips & source cards                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                     BACKEND (FastAPI)                        │
│  • Query parsing & search term extraction                    │
│  • Literature API clients (OpenAlex, Semantic Scholar)       │
│  • Text chunking pipeline                                    │
│  • OpenAI embedding service                                  │
│  • Ingest job orchestration                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ Async PostgreSQL
┌──────────────────────────▼──────────────────────────────────┐
│                  DATABASE (PostgreSQL + pgvector)            │
│  • Papers table with metadata                                │
│  • Chunks table with 1536-dim embeddings                     │
│  • Ingest jobs for progress tracking                         │
│  • HNSW index for fast similarity search                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
bio_hack/
├── frontend/                 # Next.js 16 + TypeScript
│   ├── src/
│   │   ├── app/             # App router pages
│   │   ├── components/      # React components
│   │   │   └── chat/        # Chat UI components
│   │   └── lib/             # API client & utilities
│   └── package.json
│
├── backend/                  # FastAPI + Python 3.12
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routes/          # API endpoints
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Business logic
│   │       ├── literature/  # OpenAlex & S2 clients
│   │       ├── chunking/    # Text chunking
│   │       └── embedding/   # OpenAI embeddings
│   ├── alembic/             # Database migrations
│   └── requirements.txt
│
├── docker/                   # Dockerfiles
│   ├── frontend.Dockerfile
│   ├── backend.Dockerfile
│   └── postgres.Dockerfile
│
├── docker-compose.yml        # Service orchestration
├── .env.example             # Environment template
└── README.md
```

---

## 🔌 API Reference

### Start Ingestion Job
```http
POST /api/ingest
Content-Type: application/json

{
  "query": "double slit experiment with molecules",
  "max_results_per_source": 30
}
```

### Get Job Status (for polling)
```http
GET /api/ingest/{job_id}
```

Returns real-time progress:
```json
{
  "job_id": "uuid",
  "status": "embedding",
  "progress": {
    "papers": {
      "openalex_found": 47,
      "semantic_scholar_found": 32,
      "unique_papers": 61
    },
    "chunks": { "total_created": 183 },
    "embeddings": { "completed": 120, "total": 183, "percent": 65.6 }
  }
}
```

### Other Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /documents` | List stored papers |
| `GET /chunk/stats` | Chunking statistics |
| `POST /embed/all` | Embed all chunks |
| `POST /search` | Semantic search |

Full API docs at: http://localhost:8000/docs

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings | ✅ Yes |
| `ANTHROPIC_API_KEY` | Anthropic key for synthesis | Optional |
| `OPENALEX_EMAIL` | Your email for faster API access | Optional |
| `DATABASE_URL` | PostgreSQL connection string | Auto-set |

### AI Models Used

| Task | Model | Why |
|------|-------|-----|
| Embeddings | `text-embedding-3-small` | Best value, 1536 dims |
| Query parsing | `gpt-4o-mini` | Fast, cost-effective |
| Synthesis | `gpt-4o-mini` / Claude | Configurable |

---

## 🧪 Development

### Run locally without Docker

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Run migrations
```bash
docker exec sciencerag-backend alembic upgrade head
```

### View logs
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

---

## 🎯 How It Works

### 1. User Query
```
"What are the leading interpretations of quantum mechanics since 2010?"
```

### 2. Query Parsing
Extracts search terms: `quantum mechanics interpretations`, `Copenhagen`, `many worlds`

### 3. Literature Fetch
- Queries OpenAlex and Semantic Scholar in parallel
- Deduplicates by DOI
- Stores papers with metadata

### 4. Chunking
- Splits abstracts into ~500 token chunks
- Maintains overlap for context

### 5. Embedding
- Generates 1536-dim vectors with OpenAI
- Stores in pgvector for fast similarity search

### 6. Response
- Shows papers found with citations
- Live progress in sidebar
- Expandable source cards

---

## 🏆 Built For

**Agentic Orchestration Hackathon 2026**

This project demonstrates:
- Multi-source data aggregation
- RAG pipeline architecture
- Real-time progress tracking
- Production-ready infrastructure

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [OpenAlex](https://openalex.org/) - Open scholarly metadata
- [Semantic Scholar](https://www.semanticscholar.org/) - AI-powered research tool
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity for Postgres

---

**Made with ❤️ for researchers, by researchers**
