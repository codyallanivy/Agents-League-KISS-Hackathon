# KISS Command Center — local AI dashboard

> One dark-glass cockpit over the whole system: chat with the engine, run the scope gate, watch the board, audit every reasoning trace, and see the vision board — all local-first.

```bash
cd command-center
python server.py        # → http://localhost:8765
```

The badge in the header shows which brain is on, automatically:

- **FOUNDRY:gpt-4o** — Azure endpoint configured (cloud reasoning)
- **OLLAMA:\<model\>** — local open-weight model detected (free, private; `winget install Ollama.Ollama && ollama pull qwen2.5:7b`)
- **OFFLINE** — deterministic engine (demo always works)

No frameworks, no build step, no npm — one stdlib Python file and one HTML page, wrapping the *real* Track 2 multi-agent engine (not a re-implementation). Every chat and scope check is appended to the same JSONL traces as the CLI, so the trace panel is a live audit log.
