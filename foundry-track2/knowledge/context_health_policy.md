# Context Health Policy (Synthetic adaptation)

> Source of truth for: context-cost discipline and buried-instruction risk — part of the KISS-201 curriculum. Adapted from the methodology's CONTEXT_HEALTH practice; synthetic demo content.

## The context promise

Every session's default read set stays small enough that an agent resumes cheaply without losing safety, value, or verification context. Always read: READ_FIRST.md, PROJECT_STATE.md, RISK_POLICY.md. Everything else is read when the task type requires it (see READ_FIRST.md reading sets).

## Compression rules

Safe to compress: agent-facing prose, role files, prompt recipes, long vision prose. Never compress: ITERATION_LOG.md and DECISIONS.md (audit history), TODO.md / PROJECT_STATE.md / PENDING_VERIFICATION.md (parse markers must survive), code, and human-facing guides. Compression runs on a branch with a baseline token estimate recorded and a smoke test after.

## Buried-instruction risks ("lost in the middle")

Model performance degrades on content buried mid-file. High-value memo ideas sink below older notes — promote accepted ones into TODO.md or the value ledger. Durable lessons buried in ITERATION_LOG.md history — retrospectives pull them up into AGENTS.md or RISK_POLICY.md. In large prompt files, critical rules belong near the top and mirrored in the reading-set sections.
