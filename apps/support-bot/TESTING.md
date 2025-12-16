# Support Bot Testing Guide

This guide covers how to test the support-bot locally and what scenarios to verify.

## Quick Start: Docker Compose (Recommended)

The easiest way to test everything together:

### 1. Create `.env` file

```bash
cd apps/support-bot
cp .env.example .env
```

Edit `.env` and set:
```bash
# LLM Provider (choose one)
LLM_PROVIDER=groq  # or gemini
GROQ_API_KEY=your_groq_key_here
# OR
GEMINI_API_KEY=your_gemini_key_here

# Data stores (defaults work with docker-compose)
redis_url=redis://redis:6379/0
database_url=postgresql://postgres:postgres@pgvector:5432/ai_agents

# Optional
log_level=INFO
```

### 2. Start infrastructure

From the monorepo root:

```bash
cd infra
docker-compose up -d redis pgvector
```

Wait ~10 seconds for services to be ready, then:

```bash
docker-compose up support-bot
```

The backend will be available at `http://localhost:8083`

### 3. Test the backend

#### Health check
```bash
curl http://localhost:8083/health
# Should return: {"status":"ok","service":"support-bot"}
```

#### Chat endpoint (REST)
```bash
curl -X POST http://localhost:8083/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have a billing question about my invoice",
    "session_id": "test-session-1"
  }'
```

Expected response includes:
- `response`: Bot's answer
- `intent`: `"billing"`, `"technical"`, or `"general"`
- `confidence`: Float between 0.0 and 1.0
- `escalated`: Boolean
- `ticket_id`: String (if escalated) or null
- `sources`: Array of RAG document sources

#### Test ticket creation
```bash
curl -X POST http://localhost:8083/api/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Test ticket",
    "description": "This is a test ticket",
    "intent": "technical",
    "priority": "high"
  }'
```

#### Get ticket status
```bash
# Use the ticket_id from the previous response
curl http://localhost:8083/api/tickets/{ticket_id}
```

### 4. Test the frontend

#### Setup frontend
```bash
cd apps/support-bot/frontend
npm install
```

Create `frontend/.env`:
```bash
VITE_API_URL=http://localhost:8083
VITE_WS_URL=ws://localhost:8083/api/ws
```

#### Run frontend
```bash
npm run dev
```

Open the URL shown (usually `http://localhost:5173`)

## Testing Scenarios

### 1. Intent Classification

Test that the bot correctly classifies user intents:

**Billing intent:**
```bash
curl -X POST http://localhost:8083/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need help with my invoice payment"}'
```
Expected: `"intent": "billing"`

**Technical intent:**
```bash
curl -X POST http://localhost:8083/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "The app crashes when I try to login"}'
```
Expected: `"intent": "technical"`

**General intent:**
```bash
curl -X POST http://localhost:8083/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about your product features"}'
```
Expected: `"intent": "general"`

### 2. RAG-Based Answering

**Prerequisite:** You need documents indexed in the `rag_documents` table.

If you have `rag-chat` running, you can upload documents there (they share the same table).

Test with a question that should match your indexed documents:
```bash
curl -X POST http://localhost:8083/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your refund policy?"}'
```

Check:
- `response` contains relevant information
- `sources` array lists document chunks used
- `confidence` is > 0.0

### 3. Confidence Scoring

Test that confidence scores are computed:

```bash
curl -X POST http://localhost:8083/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your pricing?"}'
```

Verify:
- `confidence` is a float between 0.0 and 1.0
- Higher confidence when RAG finds good matches
- Lower confidence when no context is available

### 4. Escalation Logic

Test escalation when confidence is low:

**Trigger low confidence** (ask something not in your knowledge base):
```bash
curl -X POST http://localhost:8083/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the meaning of life?"}'
```

If confidence < 0.65, you should see:
- `"escalated": true`
- `"ticket_id"` is a UUID string
- A ticket was created in Redis

**Verify ticket exists:**
```bash
curl http://localhost:8083/api/tickets/{ticket_id}
```

### 5. Session Memory

Test that conversation history is maintained:

```bash
# First message
curl -X POST http://localhost:8083/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My name is Alice",
    "session_id": "alice-session"
  }'

# Follow-up (should remember context)
curl -X POST http://localhost:8083/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What did I just tell you?",
    "session_id": "alice-session"
  }'
```

The bot should reference the previous message.

### 6. WebSocket Endpoint

Test real-time chat:

```javascript
// In browser console or Node.js
const ws = new WebSocket('ws://localhost:8083/api/ws');

ws.onopen = () => {
  console.log('Connected');
  ws.send(JSON.stringify({
    message: "Hello, support bot!",
    session_id: "ws-test-1"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Response:', data);
  // Should have: response, intent, confidence, escalated, ticket_id, sources
};
```

### 7. Frontend UI Testing

1. **Open the Support page** in your browser
2. **Send a message** and verify:
   - User message appears on the right (blue)
   - Bot response appears on the left (white)
   - Intent chip shows (e.g., "intent: billing")
   - Confidence percentage shows (e.g., "confidence: 75%")
3. **Test escalation**:
   - Ask something obscure to trigger low confidence
   - Verify red "escalated to human" badge appears
   - Verify Ticket ID is displayed below the message
4. **Test WebSocket**:
   - Click "Enable live updates" button
   - Send messages and verify they work over WebSocket

## Unit Tests

Run the test suite:

```bash
cd apps/support-bot
pytest
```

Tests cover:
- Health endpoint
- Confidence computation
- Escalation threshold logic
- Intent classification (billing, technical, general)

## Troubleshooting

### Backend won't start

1. **Check Redis is running:**
   ```bash
   docker-compose ps redis
   redis-cli ping  # Should return PONG
   ```

2. **Check Postgres is running:**
   ```bash
   docker-compose ps pgvector
   psql -h localhost -U postgres -d ai_agents -c "SELECT 1;"
   ```

3. **Check environment variables:**
   ```bash
   cat apps/support-bot/.env
   ```

4. **Check logs:**
   ```bash
   docker-compose logs support-bot
   ```

### Low confidence on all queries

- **No documents indexed:** Upload documents via `rag-chat` first (they share the same `rag_documents` table)
- **Embedding generator not working:** Check `GEMINI_API_KEY` is set, or it will use local hashing (lower quality)

### Frontend can't connect

- **CORS issues:** Backend CORS middleware should allow all origins in dev
- **Wrong URL:** Check `VITE_API_URL` in `frontend/.env` matches backend port (8083)
- **Backend not running:** Verify `curl http://localhost:8083/health` works

### WebSocket connection fails

- **Backend not running:** Start support-bot service
- **Wrong WebSocket URL:** Check `VITE_WS_URL` uses `ws://` (not `http://`)
- **Port mismatch:** Ensure WebSocket URL port matches backend port

## Next Steps

Once basic functionality works:

1. **Index knowledge base documents** via `rag-chat` to improve RAG answers
2. **Tune confidence threshold** in `SupportAgent.__init__` (default: 0.65)
3. **Add more intent keywords** in `simple_intent_classifier` if needed
4. **Customize escalation logic** in `EscalationAgent` for your use case
