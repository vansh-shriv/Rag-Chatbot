# VideoRAG - AI Video Analytics Chatbot

A full-stack RAG chatbot that ingests two social media videos (YouTube + Instagram), 
computes engagement analytics, and lets creators have a contextual conversation about 
their content — with streaming responses and chunk-level citations.

Built as a technical screening submission. Every output is dynamic — no hardcoded responses.

---

## what it does

- Takes a YouTube URL and an Instagram Reel URL as input
- Pulls transcripts and real metadata (views, likes, comments, engagement rate) for both
- Chunks transcripts, embeds them with BGE-small-en, stores in Qdrant with `video_label` tags
- Runs a LangGraph RAG agent (Groq Llama 3.3 70B) that retrieves from both videos separately before generating
- Streams responses token by token via FastAPI SSE
- Cites exact source chunks in every response ([Video A, Chunk 3])
- Maintains multi-turn memory across the conversation via LangGraph MemorySaver

---

## Stack Decision and Why 

Component | Choice | Why

LLM | Groq (Llama 3.3 70B) | ~800 tokens/sec, free tier, zero latency vs GPT-4o 

Embeddings | BGE-small-en-v1.5 (local) | $0 at any scale vs ~$0.002/1K tokens for OpenAI 

Vector DB | Qdrant (Docker) | Native metadata filtering, horizontal sharding, free

Orchestration | LangGraph |Stateful graph with built-in MemorySaver, cleaner than LCEL for multi-turn

Transcript | youtube-transcript-api + yt-dlp | No Whisper cost, instant, works on 99% of public videos 

Instagram stats | Apify instagram-scraper | Most reliable public scraper, $5 free credit covers hundreds of calls 

YouTube stats | YouTube Data API v3 | Official, free (10K units/day), returns real like/comment counts

---

## Cost at scale - 1000 Creators/day

This was a core design constraint. Here's the math:

**Ingestion (per video pair):**
- Transcript extraction: $0 (yt-dlp + youtube-transcript-api)
- Embedding (BGE-small local): $0 — runs on CPU, no API call
- Qdrant upsert: $0 — self-hosted Docker
- YouTube Data API: ~3 units per video, 10K free/day → covers ~3,300 videos free
- Apify Instagram: ~$0.004/run → $4/day for 1000 Reels

**Query (per chat message):**
- Groq Llama 3.3 70B: ~$0.0001/query (free tier covers most usage)
- At 10 queries/creator: ~$0.10-0.50/day for 1000 creators

**Total estimated cost: ~$5-10/day for 1000 creators**

Compare to OpenAI stack (GPT-4o + OpenAI embeddings): ~$50-80/day for same load.

**What breaks at 10,000 users:**
- Qdrant needs horizontal sharding (built-in, config change only)
- Apify becomes the bottleneck → switch to self-hosted scraper or negotiate volume pricing
- Groq free tier hits limits → switch to paid (~$0.59/1M tokens, still cheap)
- Solution: queue ingestion jobs via Celery + Redis, process async

---

## Project structure

```
RAG-Chatbot/
├── backend/
│   ├── main.py              # FastAPI app — /ingest and /chat SSE endpoints
│   ├── ingest.py            # Extraction → chunking → embedding → Qdrant pipeline
│   ├── rag_agent.py         # LangGraph graph: retrieve → generate, with MemorySaver
│   ├── extractors/
│   │   ├── youtube.py       # yt-dlp + youtube-transcript-api + YT Data API v3
│   │   └── instagram.py     # yt-dlp (caption) + Apify (real stats)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── VideoCard.jsx    # Video embed/thumbnail + metadata stats
│   │   │   ├── ChatPanel.jsx    # Streaming chat + source citation badges
│   │   │   └── IngestForm.jsx   # URL inputs + analyze button
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Local setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker Desktop running

### 1. Clone and set up backend
```bash
git clone https://github.com/vansh-shriv/Rag-chatbot.git
cd RAG-Chatbot/backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Fill in your keys (see .env.example)
```

### 3. Start Qdrant

```bash
docker compose up -d
```

### 4. Start backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

---

## API Endpoints

Method | Endpoint | Description 

POST | `/ingest` | Takes two URLs, runs full pipeline

POST | `/chat` | SSE streaming chat with RAG

GET | `/metadata` | Returns stored video metadata

GET | `/health` | Health Check

---

## Known limitations and honest trade-offs

- **Instagram thumbnail**: Instagram CDN blocks cross-origin image loads from localhost. In production, proxy the thumbnail through the backend. For demo, graceful fallback with direct link.
- **Instagram transcript**: Reels rarely have subtitles — we use the caption as the content signal. For production, pipe audio through Whisper for full transcript.
- **Follower count**: Requires a separate Apify profile call (~30s extra). Excluded from default flow for speed; architected as optional enrichment.
- **YouTube likes**: Requires YouTube Data API v3 key. Falls back gracefully if not provided.

