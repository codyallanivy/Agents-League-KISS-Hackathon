"""Base agent: grounded prompting, Microsoft Foundry model client with offline
fallback, and full JSONL reasoning-trace logging (every prompt, grounding
source, and output is queryable later via query.py).
"""

import json
import os
import time
import uuid
from pathlib import Path

TRACE_DIR = Path(__file__).resolve().parent.parent / "traces"


class TraceLogger:
    """Append-only JSONL trace of every agent step in a run."""

    def __init__(self, run_id=None):
        TRACE_DIR.mkdir(exist_ok=True)
        self.run_id = run_id or time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
        self.path = TRACE_DIR / f"run-{self.run_id}.jsonl"

    def log(self, **record):
        record["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        record["run_id"] = self.run_id
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


class ModelClient:
    """Microsoft Foundry chat client. Falls back to None (offline deterministic
    reasoning) when no endpoint is configured — the demo always runs."""

    def __init__(self):
        self.endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "").strip()
        self.deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4o")
        self._openai = None
        if self.endpoint:
            try:
                from azure.ai.projects import AIProjectClient
                from azure.identity import DefaultAzureCredential
                project = AIProjectClient(endpoint=self.endpoint,
                                          credential=DefaultAzureCredential())
                # azure-ai-projects >= 1.0: OpenAI-compatible chat client
                self._openai = project.get_openai_client(api_version="2024-10-21")
            except Exception as exc:  # missing SDK, no az login, quota, etc.
                print(f"[warn] Foundry unavailable ({type(exc).__name__}: {exc}) — offline reasoning mode.")

        # Tier 2: local open-weight model via Ollama (free, private, offline).
        # See research: "Community Open Model Path" — local inference first.
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self._ollama = False
        if not self._openai:
            try:
                import urllib.request
                req = urllib.request.urlopen(self.ollama_url + "/api/tags", timeout=1.5)
                tags = json.loads(req.read().decode())
                names = [m.get("name", "") for m in tags.get("models", [])]
                if names:
                    if not any(self.ollama_model in n for n in names):
                        self.ollama_model = names[0]
                    self._ollama = True
            except Exception:
                pass  # no local model server — deterministic tier

    @property
    def mode(self):
        if self._openai:
            return f"foundry:{self.deployment}"
        if self._ollama:
            return f"ollama:{self.ollama_model}"
        return "offline"

    def _ollama_complete(self, system, user):
        import urllib.request
        body = json.dumps({"model": self.ollama_model, "stream": False,
                           "messages": [{"role": "system", "content": system},
                                        {"role": "user", "content": user}]}).encode()
        req = urllib.request.Request(self.ollama_url + "/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode())["message"]["content"]

    def complete(self, system, user):
        if self._ollama:
            try:
                return self._ollama_complete(system, user)
            except Exception as exc:
                print(f"[warn] Ollama call failed ({exc}) — deterministic fallback.")
                return None
        if not self._openai:
            return None
        try:
            resp = self._openai.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                temperature=0.2,
            )
            return resp.choices[0].message.content
        except Exception as exc:
            print(f"[warn] Foundry call failed ({exc}) — offline fallback for this step.")
            return None


class AgentContext:
    """Shared services handed to every agent."""

    def __init__(self, foundry_iq, fabric_iq, work_iq, model=None, tracer=None):
        self.foundry_iq = foundry_iq
        self.fabric_iq = fabric_iq
        self.work_iq = work_iq
        self.model = model or ModelClient()
        self.tracer = tracer or TraceLogger()


class BaseAgent:
    name = "BaseAgent"
    instructions = "You are a helpful agent."

    def __init__(self, ctx: AgentContext):
        self.ctx = ctx

    def grounded_prompt(self, task: str, grounding: list) -> str:
        cites = "\n\n".join(
            f"[{g['citation']}]\n{g['snippet']}" for g in grounding) or "(none)"
        return (f"TASK:\n{task}\n\nGROUNDED KNOWLEDGE (cite by source):\n{cites}\n\n"
                "Answer concisely. Every claim must cite a grounding source in [brackets]. "
                "If grounding is insufficient, say so rather than inventing facts.")

    def execute(self, task: str, grounding: list, offline_fn, extra=None):
        """Run via Foundry model if available, else deterministic offline logic.
        Either way the full step is traced."""
        user = self.grounded_prompt(task, grounding)
        raw = self.ctx.model.complete(self.instructions, user)
        if raw is not None:
            result = {"answer": raw}
        else:
            result = offline_fn()
        result.setdefault("citations", [g["citation"] for g in grounding])
        self.ctx.tracer.log(
            agent=self.name,
            model=self.ctx.model.mode,
            prompt={"system": self.instructions, "user": user},
            grounding=[g["citation"] for g in grounding],
            output=result,
            extra=extra or {},
        )
        return result
