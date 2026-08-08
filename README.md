# AI Interview Agent

A production-grade AI-powered technical interviewer for the 31-day AI Engineering Cohort. Conducts adaptive, multi-turn technical interviews personalized to each candidate's learning journey.

> **Build the interviewer, not the interview.**

---

## Architecture

```
┌─────────────────────────────────────┐
│     POST /api/interview (FastAPI)    │
└──────────────────┬──────────────────┘
                   │
┌──────────────────┴──────────────────┐
│        Interview Service             │
│   (State Machine + Orchestration)    │
└──────────────────┬──────────────────┘
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐
│Candidate│  │Curriculum │  │  RAG         │
│Analyzer │  │ Service   │  │  Retriever   │
└─────────┘  └──────────┘  └──────────────┘
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Question │ │Evaluation│ │ Feedback │
│ Planner  │ │ Service  │ │Generator │
└──────────┘ └──────────┘ └──────────┘
                   │
         ┌─────────────────┐
         │   LLM Provider   │
         │(OpenRouter/Groq/..)│
         └─────────────────┘
```

---

## Features

- **Adaptive Questioning** — Questions adapt based on candidate strengths, weaknesses, and answer quality
- **RAG-Grounded** — Curriculum chunked into 155 pieces, retrieved before each question for curriculum-accurate content
- **State Machine** — Explicit interview phases (Introduction → Baseline → Deep Dive → Challenge → Final Review)
- **Coverage Tracking** — Ensures minimum 8 questions across 4+ curriculum days
- **Difficulty Adaptation** — Dynamic 1-5 scale based on demonstrated performance
- **Anti-Repetition** — TF-IDF similarity prevents asking the same thing twice
- **Evidence-Based Scoring** — Every score backed by specific interview evidence
- **Misconception & Claim Tracking** — Detects questionable claims, revisits them later
- **Prompt Injection Resistant** — Sanitizes input, ignores manipulation attempts
- **Multi-Provider LLM** — Supports OpenRouter, Groq, OpenAI, Gemini, Ollama
- **Technical Spec Compliant** — Single `POST /api/interview` endpoint with sessionId-based state

---

## API Contract

Single endpoint as per Technical Specification:

```
POST /api/interview
```

### Start Interview

```json
{
  "sessionId": "abc-123",
  "candidate": { "candidate_id": "candidate_001" }
}
```

Response:
```json
{
  "reply": "Let's start with something you've built...",
  "done": false
}
```

### Conversation Turn

```json
{
  "sessionId": "abc-123",
  "message": "I built a RAG system using..."
}
```

Response:
```json
{
  "reply": "Good. Now suppose retrieval is returning irrelevant chunks...",
  "done": false
}
```

### End Interview

When the interview completes naturally:
```json
{
  "reply": "Thank you for completing the interview.",
  "done": true,
  "feedback": {
    "summary": "Strong performance in RAG and retrieval...",
    "strengths": ["RAG architecture design", "Debugging methodology"],
    "gaps": ["Deployment and observability", "Cost optimization"],
    "next": ["Day 18: Review deployment strategies", "Day 19: Set up monitoring"]
  }
}
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- An OpenRouter API key (free tier available)

### Setup

```bash
git clone https://github.com/iittjjee2024/AI-Interview-Agent.git
cd AI-Interview-Agent
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env — add your LLM_API_KEY
```

### Run Backend

```bash
python -m uvicorn app.main:app --reload
```

Server starts at `http://localhost:8000`

### Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend at `http://localhost:5173` — proxies API calls to backend.

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (openrouter, groq, openai, gemini, ollama) | openrouter |
| `LLM_MODEL` | Model identifier | google/gemma-4-26b-a4b-it:free |
| `LLM_API_KEY` | API key for LLM provider | |
| `LLM_TIMEOUT` | Request timeout in seconds | 60 |
| `MIN_QUESTIONS` | Minimum questions before ending | 8 |
| `MAX_QUESTIONS` | Hard maximum questions | 15 |
| `MIN_CURRICULUM_DAYS` | Minimum curriculum days to cover | 4 |
| `QUESTION_SIMILARITY_THRESHOLD` | Repetition detection threshold | 0.85 |

---

## How It Works

### Interview Flow

```
Start → Load Candidate Profile → Analyze Strengths/Weaknesses
  ↓
RAG: Retrieve relevant curriculum chunks → Generate Opening Question
  ↓
Candidate Answers → Evaluate (correctness, depth, reasoning) → Extract Claims
  ↓
Plan Next Question (coverage scoring, difficulty adaptation)
  ↓
RAG: Retrieve context for next topic → Generate Adaptive Follow-up
  ↓
Repeat until: min questions + min coverage + sufficient evidence
  ↓
Generate Structured Feedback (summary, strengths, gaps, next steps)
```

### RAG Pipeline

```
Curriculum JSON (31 days)
       ↓
Chunking (overview, objectives, concepts, tools, skills per day)
       ↓
155 Chunks indexed with TF-IDF
       ↓
Query: concept + skill_dimension + difficulty
       ↓
Top-4 relevant chunks → Injected into LLM prompt
       ↓
Curriculum-grounded question generation
```

### Candidate Analysis

The system classifies candidate knowledge into:
- **Strong areas** — High scores, few attempts, strong learning signals
- **Weak areas** — Low scores, many attempts, confusion signals
- **Skipped areas** — Not penalized but noted as unverified
- **Unknown areas** — No evidence either way

---

## Project Structure

```
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── api/
│   │   ├── routes/interview.py  # POST /api/interview endpoint
│   │   ├── routes/health.py     # Health check
│   │   └── dependencies.py      # Dependency injection
│   ├── core/
│   │   ├── config.py            # Settings from .env
│   │   ├── logging.py           # Structured logging
│   │   └── security.py          # Input sanitization
│   ├── domain/
│   │   ├── models.py            # Pydantic data models
│   │   ├── enums.py             # State machine states, question types
│   │   └── schemas.py           # API schemas
│   ├── services/
│   │   ├── interview_service.py # Main orchestrator
│   │   ├── question_service.py  # Planning, scoring, anti-repetition
│   │   ├── evaluation_service.py# Answer evaluation via LLM
│   │   ├── curriculum_service.py# Curriculum loading
│   │   └── candidate_service.py # Candidate analysis
│   ├── retrieval/
│   │   ├── curriculum_retriever.py  # RAG: chunk, index, retrieve
│   │   └── embeddings.py           # TF-IDF embedding service
│   ├── memory/
│   │   ├── repositories.py     # In-memory state storage
│   │   └── breeth_memory.py    # Breeth API integration
│   ├── llm/
│   │   ├── base.py             # Provider interface
│   │   ├── factory.py          # Provider factory
│   │   └── providers/          # OpenRouter, Groq, OpenAI, Gemini
│   └── prompts/                # Prompt templates
├── data/
│   ├── curriculum.json         # 31-day curriculum
│   └── candidates.json         # Candidate profiles
├── frontend/                   # React + TypeScript + Tailwind
├── tests/                      # Unit + integration tests
├── scripts/                    # Test and utility scripts
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── technical-spec.md           # API contract specification
```

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Unit tests only
python -m pytest tests/unit/ -v

# Integration test (uses mock LLM)
python -m pytest tests/integration/ -v
```

---

## Docker

```bash
docker compose up --build
```

---

## Design Decisions

1. **Single endpoint** — Matches technical spec exactly. Session state managed by `sessionId`.
2. **RAG with TF-IDF** — Lightweight, no external vector DB needed. 155 curriculum chunks provide grounded context.
3. **Separate evaluation and generation** — Two focused LLM calls per turn, each with its own prompt and temperature.
4. **OpenRouter as default** — Free tier models available, easy provider switching.
5. **In-memory state** — Simple for hackathon scope, repository interface allows swap to Redis/PostgreSQL.
6. **Deterministic planning + LLM generation** — Question selection scored algorithmically, then LLM makes it conversational.

---

## Supported LLM Providers

| Provider | Config Value | Example Model |
|----------|-------------|---------------|
| OpenRouter | `openrouter` | `google/gemma-4-26b-a4b-it:free` |
| Groq | `groq` | `llama-3.3-70b-versatile` |
| OpenAI | `openai` | `gpt-4o` |
| Google Gemini | `gemini` | `gemini-1.5-flash` |
| Ollama (local) | `ollama` | `llama3` |
