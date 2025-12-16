# Support Bot

AI-powered customer support bot built on top of the shared `core` package.
It uses RAG over PGVector, intent classification, confidence scoring, and
automatic escalation to human agents via a mock ticketing system.

## Architecture

- **Backend**: FastAPI (`apps/support-bot/app`)
  - `main.py`: FastAPI app wiring, health, routers, scheduler startup.
  - `routers/support_router.py`:
    - `POST /api/chat` – main chat endpoint.
    - `POST /api/tickets` – create a ticket explicitly.
    - `GET /api/tickets/{ticket_id}` – check ticket status.
    - `WebSocket /api/ws` – realtime chat endpoint.
  - `services/support_service.py`:
    - Wires `LLM`, `RedisSessionMemory`, `PGVectorStore`, `EmbeddingGenerator`,
      `ToolRegistry`, and `SupportAgent`.
  - `agents/support_agent.py`:
    - `IntentClassifierAgent` – classifies into `billing`, `technical`, `general`.
    - `AnswerAgent` – RAG-based answer with PGVector + embeddings.
    - `EscalationAgent` – decides escalation and creates tickets via tools.
    - `SupportAgent` – orchestrates the above into a single response.
  - `tools/support_tools.py`:
    - `CreateTicketTool` – mock ticket creation in Redis.
    - `GetTicketStatusTool` – fetch ticket details from Redis.
  - `models/support_models.py`:
    - Pydantic models for chat and ticketing (requests/responses).

- **Frontend**: React + Vite + Tailwind (`apps/support-bot/frontend`)
  - `src/pages/Support.jsx`: chat UI with escalation indicator & ticket ID.
  - Uses `VITE_API_URL` and `VITE_WS_URL` for backend URLs.

- **Shared core** (`packages/core/core`):
  - `LLM` – multi-provider wrapper (Groq, Gemini).
  - `RedisSessionMemory` – conversation history and session storage.
  - `EmbeddingGenerator` – embeddings with Gemini or local hashing fallback.
  - `PGVectorStore` – vector DB based on `pgvector` in Postgres.
  - `ToolRegistry` and `Tool` base classes – for ticketing tools.

## Environment variables

Backend (`apps/support-bot/.env`):

- **LLM / providers**
  - `LLM_PROVIDER` – `groq` or `gemini` (defaults to `groq`).
  - `GROQ_API_KEY` – required when using Groq.
  - `GROQ_MODEL` – optional override of the Groq model.
  - `GEMINI_API_KEY` – required when using Gemini.

- **Data stores**
  - `redis_url` – Redis URL for session memory & tickets
    - default: `redis://localhost:6379/0`
  - `database_url` – Postgres URL used by PGVector
    - default: `postgresql://postgres:postgres@localhost:5432/ai_agents`

Frontend (`apps/support-bot/frontend/.env`):

- `VITE_API_URL` – base URL of the support-bot backend
  - e.g. `http://localhost:8000`
- `VITE_WS_URL` – WebSocket URL
  - e.g. `ws://localhost:8000/api/ws`

## Escalation logic

1. **Intent classification**
   - `IntentClassifierAgent` uses a deterministic keyword-based classifier
     (`billing`, `technical`, `general`) and stores the intent in Redis
     conversation history.

2. **Answer generation (RAG)**
   - `AnswerAgent`:
     - Generates an embedding for the user query.
     - Queries `PGVectorStore` (table `rag_documents`) to retrieve context.
     - Builds a structured prompt with system instructions, history, and context.
     - Calls the LLM to generate an answer.
     - Computes:
       - `retrieval_confidence` – based on the top similarity score from PGVector
         (0–1).
       - `self_eval_confidence` – by asking the LLM to rate its own answer on a
         0–1 scale.
       - `confidence` – the average of `retrieval_confidence` and
         `self_eval_confidence`.

3. **Escalation decision**
   - `EscalationAgent` receives:
     - `intent`, `confidence`, `query`, `answer`, `session_id`, `user_id`.
   - If `confidence < 0.65`, it:
     - Constructs a ticket subject and description from the conversation.
     - Calls `CreateTicketTool` via the `ToolRegistry`.
     - Writes an escalation message into the session history.
     - Returns `{escalated: True, ticket_id: ...}`.
   - Otherwise it returns `{escalated: False, ticket_id: None}`.

4. **Final response to the client**
   - `SupportAgent` merges all parts into a `SupportChatResponse`:
     - `response`, `intent`, `confidence`, `escalated`, `ticket_id`, `sources`.

## Running locally

### Backend

1. Install dependencies from the monorepo root (example):

```bash
pip install -e packages/core
pip install -e apps/support-bot
```

2. Copy `.env.example` to `.env` inside `apps/support-bot` and adjust values.

3. Ensure Postgres and Redis are running (or use the existing `docker-compose`).

4. Run the API:

```bash
cd apps/support-bot
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

1. Install dependencies:

```bash
cd apps/support-bot/frontend
npm install
```

2. Create `.env` with:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/api/ws
```

3. Start the dev server:

```bash
npm run dev
```

The Support Bot UI will show:

- Chat transcript.
- Intent chips and confidence percentage for bot messages.
- A clear red **“escalated to human”** indicator when confidence is low.
- The created **Ticket ID** for escalated conversations.


