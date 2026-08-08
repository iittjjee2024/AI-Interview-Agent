# Project Prompts — AI Interview Agent

These are the actual prompts and thought process used throughout development — from idea to deployment. Written as a human developer would naturally think, including the real errors hit and tools chosen.

---

## STAGE 1: IDEA & CONCEPT

### Prompt 1 — The spark
"I need to build an AI that interviews people about what they learned in a 31-day AI cohort. Not a dumb quiz — something that actually listens, follows up, and feels like talking to a real senior engineer."

### Prompt 2 — What's wrong with existing solutions
"Every interview bot just asks 10 canned questions in order. That's useless. A real interviewer adapts — if you give a great answer about RAG, they push harder. If you struggle with deployment, they don't keep piling on, they simplify."

### Prompt 3 — The core principle
"Build the interviewer, not the interview. The system should decide what to ask dynamically based on who the candidate is, what they've done, and how they're answering right now."

---

## STAGE 2: PLANNING & ARCHITECTURE

### Prompt 4 — Tech stack decision
"Going with Python FastAPI for the backend because it's async, fast, and has great Pydantic integration for validation. React with Tailwind for frontend — simple, no over-engineering. OpenRouter for LLM so I can use free models and swap providers without code changes."

### Prompt 5 — The single endpoint insight
"The technical spec says one endpoint: POST /api/interview. First call sends sessionId + candidate to start, subsequent calls send sessionId + message. I need to detect which is which in the same handler. Clean."

### Prompt 6 — Why separate evaluation from generation
"I realized early on that one giant prompt doing everything would be unreliable. Split it: one LLM call evaluates the answer (structured JSON output), another generates the next question (natural language). Each prompt is focused and testable."

### Prompt 7 — RAG or no RAG
"At first I thought just passing the curriculum day info to the LLM would be enough. But with 31 days of content, I can't fit it all in context. Solution: chunk the curriculum into 155 pieces, index them, retrieve only what's relevant for each question. That's RAG."

---

## STAGE 3: TOOLS & TECHNOLOGY CHOICES

### Prompt 8 — Why TF-IDF over embeddings API
"I could use OpenAI embeddings or sentence-transformers, but that adds a dependency and costs money per call. TF-IDF with scikit-learn is free, fast, deterministic, and good enough for matching curriculum chunks to topics. I'll upgrade later if needed."

### Prompt 9 — Why Pydantic everywhere
"Every internal data structure is a Pydantic model — InterviewSession, CandidateProfile, AnswerEvaluation, QuestionPlan. This means validation is automatic, serialization is free, and I catch bugs at the boundary instead of deep in business logic."

### Prompt 10 — Why in-memory state
"For a hackathon, I don't need PostgreSQL. But I built a repository interface so swapping to Redis or Postgres later is just implementing the same async methods. The InMemoryInterviewRepository works fine for demos."

### Prompt 11 — OpenRouter as the LLM gateway
"OpenRouter gives me access to free models like Gemma and lets me switch between providers with one config change. The API is OpenAI-compatible so my existing OpenAIProvider class works as-is — just change the base URL."

### Prompt 12 — Structlog for observability
"Using structlog instead of plain logging because it outputs structured JSON in production. Every LLM call logs interview_id, question_id, latency, and token usage. Makes debugging way easier than grepping through unstructured text."

---

## STAGE 4: IMPLEMENTATION DECISIONS

### Prompt 13 — The state machine isn't linear
"I defined states like INTRODUCTION, BASELINE_ASSESSMENT, DEEP_DIVE, CHALLENGE, WEAKNESS_PROBE, FINAL_REVIEW. But the transitions aren't sequential — if a candidate gives an excellent answer during baseline, I jump straight to CHALLENGE. If they struggle in deep dive, I drop to WEAKNESS_PROBE."

### Prompt 14 — Question scoring algorithm
"Before asking the LLM to generate a question, I score potential topics: coverage_need + weakness_priority + curriculum_relevance + difficulty_fit - repetition_penalty - already_covered_penalty. This ensures algorithmic diversity, then the LLM makes it conversational."

### Prompt 15 — Difficulty as a number not a vibe
"Difficulty 1-5. Level 1 is definitions, level 5 is production architecture under constraints. I track it explicitly and adapt: strong answer bumps up, weak answer bumps down. Bounded so it never goes below 1 or above 5."

### Prompt 16 — Anti-repetition with similarity threshold
"After generating a question, I check cosine similarity against all previous questions using TF-IDF vectors. If > 0.85, I regenerate with higher temperature. Three attempts max, then accept whatever we get. The interview never freezes."

### Prompt 17 — Claim tracking for realistic interviews
"When a candidate says 'vector search always outperforms keyword search', I store that as a questionable claim. Three turns later, I can circle back: 'You mentioned earlier that vector search always wins — can you think of a case where that breaks down?' This is how real interviewers work."

---

## STAGE 5: ERRORS ENCOUNTERED & SOLUTIONS

### Prompt 18 — The missing import crash
"Got a 500 error on interview start: 'name QuestionType is not defined'. I used QuestionType in the opening question generator but forgot to import it when I refactored interview_service.py. Lesson: always check imports after moving code between files."

### Prompt 19 — Groq model decommissioned
"The server returned 400: 'The model llama-3.1-70b-versatile has been decommissioned'. Groq deprecated it without warning. Fixed by switching to llama-3.3-70b-versatile. Then later switched to OpenRouter entirely for more stability with free models."

### Prompt 20 — The stale environment variable nightmare
"Spent 20 minutes debugging why my .env file wasn't being read. Turns out there was a process-level LLM_API_KEY environment variable set in my terminal session with a garbage value. It was overriding the .env file because pydantic-settings gives env vars priority. Fixed by explicitly loading dotenv values with priority in the config loader."

### Prompt 21 — Pydantic uppercase vs lowercase keys
"When I tried passing dotenv values as kwargs to Settings(), I got 'Extra inputs are not permitted' for APP_ENV, LLM_PROVIDER etc. The .env file has UPPERCASE keys but Pydantic field names are lowercase. Simple fix: lowercase all keys before passing them in."

### Prompt 22 — GitHub push protection blocking the push
"First push was rejected: 'Push cannot contain secrets — Groq API Key detected in scripts/test_groq.py:5'. I'd hardcoded the key in a test script. Fixed by replacing it with a placeholder, amended the commit, and pushed again. Never hardcode keys, even in test scripts."

### Prompt 23 — JSON parsing from LLM responses
"The evaluator was returning 0.5 for everything. The LLM was wrapping its JSON in markdown code blocks (```json ... ```). Added stripping logic to handle this. Also added a fallback: find the first { and last } in the response and try parsing that substring."

### Prompt 24 — Free model timeout issues
"The OpenRouter free model (gemma-4-26b) takes ~30 seconds per call. With two calls per turn (evaluate + generate), that's 60 seconds. Had to increase LLM_TIMEOUT from 30 to 60 in .env. For production, I'd use a paid model or parallelize the calls."

---

## STAGE 6: TESTING APPROACH

### Prompt 25 — What to unit test
"I test the things that should be deterministic: Does the question planner pick uncovered days? Does difficulty stay bounded 1-5? Does the similarity detector catch near-duplicates? Does the security module flag prompt injection? These all work without an LLM."

### Prompt 26 — Integration tests with mocked LLM
"For API tests, I mock the LLM provider to return canned responses. This lets me verify the full request/response cycle — start interview, submit answer, get next question — without burning API credits or dealing with nondeterministic outputs."

### Prompt 27 — Live testing with real models
"I wrote scripts/test_live.py that runs a real 3-turn interview against the actual LLM. It verifies: opening references the candidate's project, follow-up adapts to answer quality, topics change between turns. This catches integration issues mocks can't find."

---

## STAGE 7: DEPLOYMENT READINESS

### Prompt 28 — Docker for reproducibility
"Multi-stage Dockerfile: builder stage installs deps, production stage copies them in with a non-root user. Health check pings /health. Image is slim because it only contains runtime deps + app code + data files. No test fixtures or dev tools."

### Prompt 29 — The .env.example contract
"Every environment variable the app needs is documented in .env.example with sensible defaults. A new developer can cp .env.example .env, add their API key, and run. No guessing what config exists."

### Prompt 30 — Final deployment checklist
"Before shipping I verify: 17 unit tests pass, API matches the technical spec (single POST /api/interview), candidate profiles load from both stored JSON and request payload, feedback returns summary/strengths/gaps/next arrays, prompt injection gets silently ignored, and the whole thing runs in Docker."


---

## STAGE 8: PRODUCTION ERRORS & FIXES (Post-Deployment)

### Prompt 31 — Render health check returning 404
"Deployed to Render but the health check was hitting GET / and getting 404. I had /health but not /. Fixed by either adding a root route or letting the frontend handle it. Then realized the root route was conflicting with the frontend SPA — removed it and let the catch-all serve index.html at /."

### Prompt 32 — Frontend showing 'Unknown' candidates with 0 missions
"The frontend loaded but showed 3 'Unknown' entries with 0y exp. The problem: the Dockerfile only copied data/candidates.json (old dev format with 3 fake candidates), not the root candidates.json (real 20-candidate hackathon data). Fixed by adding COPY candidates.json to Dockerfile and fixing the path resolution to search multiple locations."

### Prompt 33 — NoneType has no attribute 'completed_missions'
"This was the nastiest bug. Interview would START fine but crash on the second request. The CandidateService was loading from data/candidates.json (old format, keys like candidate_001) but the session stored candidate_id as CAND-001. When submit_answer called get_candidate('CAND-001'), it returned None. The fix: rewrote CandidateService.load() to find the real candidates.json and parse the {member, missions, signals} format."

### Prompt 34 — Curriculum validation failing with 'module field required'
"The CurriculumDay Pydantic model had module and topic as required fields. But the real curriculum.json uses 'title' and 'type' instead. Pydantic threw a validation error during load. Fixed by making module/topic optional with defaults, and normalizing the data on load — mapping title→topic, type→module, objectives→learning_objectives."

### Prompt 35 — Two different data formats, one codebase
"The hackathon gave us candidates.json and curriculum.json in their own format. I had built the system against a different format during development. Rather than rewrite everything, I added a normalization layer in both services that detects which format it's reading and transforms it to the internal schema. Now it works with either."

### Prompt 36 — Docker path resolution mismatch
"Locally, Path('candidates.json') resolves fine because CWD is the project root. In Docker, the working dir is /app but the file is at /app/candidates.json — same thing. BUT the issue was that Path(__file__).parent.parent led to different locations depending on module depth. Fixed by trying multiple path strategies: __file__ relative, CWD-relative, and hardcoded data/ fallback."

### Prompt 37 — Frontend proxy ECONNREFUSED
"Frontend on port 5173 was proxying to localhost:8000 but backend wasn't running. The Vite proxy just throws ECONNREFUSED with no helpful message. The solution for production: don't use a proxy at all — build the React app and serve it directly from FastAPI using StaticFiles + a catch-all route. One server, one port, no proxy issues."

### Prompt 38 — Render deploying stale builds
"I pushed a fix but Render kept showing the old error. Turns out Render caches Docker layers aggressively. The fix was already in the repo — I just had to wait for the full rebuild to complete. Lesson: check the Render deploy logs to confirm your commit SHA matches what's being built."
