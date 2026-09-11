# Routing Taxonomy

Use this table to classify each task in a workload. When a task matches multiple tiers, use the highest tier.

---

## Tier 1 — Cheap (haiku or equivalent)

**Characteristics:** Short output, structured extraction, rule-following, no novel reasoning.

| Pattern | Examples |
|---------|----------|
| Classification / labeling | Classify intent, sentiment, priority |
| Extraction | Extract order number, named entities, field values from structured text |
| Formatting / transformation | Reformat JSON, convert units, apply template |
| Short summarization | Summarize a paragraph or short doc (< 500 words) |
| Yes/no / boolean decisions | Does this text contain a phone number? Is this message spam? |
| Lookup / retrieval assist | Answer from a provided context block (no reasoning beyond retrieval) |
| Translation (short, technical) | Translate a UI label or error message |
| Template fill | Fill in a form template from structured input |

---

## Tier 2 — Mid (sonnet or equivalent)

**Characteristics:** Code output, moderate reasoning, domain knowledge application, moderate output length.

| Pattern | Examples |
|---------|----------|
| Code generation | Add a button, implement a function, write a test |
| Bug fixing | Fix a specific error given code + stack trace |
| Code review (single file) | Review a pull request, suggest improvements |
| Test writing | Write unit tests for a given function |
| Moderate summarization | Summarize a long document, meeting notes |
| Analysis | Analyze log output, profile results, benchmark data |
| Migration (mechanical) | Migrate API calls from v1 to v2 following a guide |
| Integration | Wire up a new endpoint, add a third-party SDK |
| Explanation / documentation | Explain a function, write a docstring |
| Refactoring (bounded scope) | Refactor a single module or function |

---

## Tier 3 — Frontier (opus or equivalent)

**Characteristics:** Novel problem-solving, multi-constraint optimization, ambiguous requirements, cross-system reasoning, long context synthesis.

| Pattern | Examples |
|---------|----------|
| Architecture design | Design a distributed system, choose tech stack with trade-offs |
| Novel algorithm | Create a new algorithm for a specific constraint set |
| Complex refactoring | Refactor an entire codebase or architectural layer |
| Multi-step agentic planning | Plan a long sequence of steps with dependencies and contingencies |
| Ambiguous intent resolution | Interpret vague or conflicting requirements into a concrete plan |
| Cross-system reasoning | Reason across multiple codebases, APIs, and data stores simultaneously |
| Performance optimization (deep) | Profile + redesign bottlenecks in a complex pipeline |
| Security audit | Comprehensive security analysis requiring expert knowledge |
| Research synthesis | Synthesize information from multiple long documents into novel conclusions |

---

## Agent Loop Detection

Flag session pinning as **required** if any of these are true:

- Tasks run in a multi-turn conversation (the agent sends multiple requests in a session)
- Tool call outputs are fed back into the prompt (read file → edit file → verify)
- Iterative refinement: test → fix → test loops
- Session state accumulates: system prompt + history grows across turns
- The prompt mentions "agent", "loop", "iterate", "pipeline", "workflow"

When session pinning is required, all tasks in the session should use the same model — choose the tier of the **hardest task** in the session.
