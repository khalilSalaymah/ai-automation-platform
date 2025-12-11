# Core Package

Shared utilities and base classes for the AI agent framework.

## Installation

```bash
pip install -e .
```

## Modules

- `llm.py` - Multi-provider LLM wrapper (Groq, Gemini) with function calling support
- `memory.py` - Redis-based session memory
- `tools.py` - Tool registry and standardized tool interface
- `embeddings.py` - Vector store abstraction
- `agents.py` - Base agent classes and orchestrator
- `logger.py` - Loguru-based logging
- `config.py` - Configuration management
- `errors.py` - Custom exception classes
- `vectorstore/` - PGVector and Pinecone implementations

