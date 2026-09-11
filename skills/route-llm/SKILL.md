---
name: route-llm
description: >
  Analyze an LLM workload and produce a routing table mapping tasks to model
  tiers (cheap/mid/frontier) with cost estimates and session-pinning guidance.
  Provider-agnostic: auto-detects Anthropic, OpenAI, Ollama, Azure. Models
  discovered from provider API — no hardcoded model IDs. Works with always-on mode:
  /route-llm on prepends a routing header to every response.
license: Apache-2.0
metadata:
  author: sap-ux
  version: "2.0"
---

> ## ⚠️ READ FIRST — MODE DETECTION
> Parse `$ARGUMENTS` and the current prompt:
> - Contains "on" → **Activation Flow**
> - Contains "off" OR prompt says "stop routing" / "route-llm off" → **Deactivation Flow**
> - Otherwise → **One-Shot Analysis**

---

## Mode 1: One-Shot Analysis

**Trigger:** `/route-llm [workload description]`

Execute all 5 steps in order without stopping.

**Step 1 — Identify task types.** Parse the workload description. List every distinct operation the LLM is asked to perform.

**Step 2 — Classify each task** using [references/routing-taxonomy.md](references/routing-taxonomy.md).

**Step 3 — Detect agent loop.** If tasks run in multi-turn context, iterative tool-call loops, or session state accumulates across turns → session pinning is required. Read [references/cost-math.md](references/cost-math.md) for cache math.

**Step 4 — Calculate blended cost** using [references/cost-math.md](references/cost-math.md).

**Step 5 — Output** in this exact format:

```
## Task Classification
| Task | Tier | Rationale |
|------|------|-----------|

## Routing Table
| Task | Tier | Model | Notes |
|------|------|-------|-------|

## Session Pinning
[Required / Not required] — [reason. If required: explain cache savings lost per model switch]

## Cost Estimate
Blended: ~$X.XX/M tokens vs single-model ~$Y.YY/M (~Z% reduction)

## Implementation Notes
[Provider-agnostic implementation guidance. Mention session-pinning API pattern if relevant.]
```

---

## Mode 2: Activation Flow

**Trigger:** `/route-llm on`

Run these steps:

1. Run the activation script:
   ```bash
   bash skills/route-llm/scripts/activate.sh
   ```

2. Confirm to the user:
   > **Routing mode active.** Task tier and model recommendation are pre-classified on every prompt.
   > Auto-detects your provider (Anthropic, OpenAI, Ollama, Azure). Models discovered from provider API.
   > 
   > Questions proceed immediately with Tier 1 model — no pause.
   > Implementation tasks pause and ask you to pin a model for the entire task to maximize cache savings.
   >
   > - Claude Code users: `/model <name>` to switch
   > - Other tools: switch model in your tool settings
   > - Deactivate: `stop routing` or `/route-llm off`
   >
   > **Restart your tool** for the hook to take effect if this is first activation.

---

## Provider Support

route-llm automatically detects and supports:

| Provider | Detection | Model discovery | Switch command |
|----------|-----------|-----------------|---|
| **Anthropic** | `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` | Name heuristics (claude-*) | `/model {model}` (Claude Code CLI) |
| **OpenAI** | `OPENAI_API_KEY` | API: `GET /v1/models` | Manual switch in tool |
| **Ollama** | `localhost:11434` (port check) | API: `GET /api/tags` | Manual switch in tool |
| **Azure** | `AZURE_OPENAI_API_KEY` | API: `GET /deployments` | Manual switch in tool |
| **Unknown** | None of the above | Tier labels only (no model names) | — |

**Zero-config install:** Just activate. route-llm detects your provider from environment variables.

**Dynamic models:** New models are automatically classified into tiers based on name heuristics
(mini/nano → Tier 1, opus/70b → Tier 3, mid-tier default). No hardcoded model IDs means
route-llm works with future models without code changes.

**Override provider (advanced):** Set `ROUTE_LLM_PROVIDER=<name>` to force a specific provider.

**Cache:** Model configurations are cached at `~/.route-llm/config.json` (machine-level, not project).
Cache invalidates after 7 days and auto-rediscovers.

---

## Session Pinning Strategy (cache efficiency)

**Goal:** Maximize prompt cache reuse. Avoid mid-task model switches that destroy cached context.

**How it works:**

- **Cache TTL:** 5 minutes per request. Cached tokens cost 90% less.
- **Cache miss on switch:** Changing models resets cache. Full context re-billed at new model's input rates.
- **Solution:** Pin one model per task. Context accumulates in cache across all turns. No re-billing.

**Cost impact:**

| Scenario | Pin Model | Switch Mid-Task | Savings |
|----------|-----------|-----------------|---------|
| Clarify then implement (7k context, 10 turns) | ~$0.108 | ~$0.125 | 13% |
| Pure exploration (7k context, 5 turns) | ~$0.012 | ~$0.045 | 73% |
| Large context (50k tokens, 20 turns) | ~$0.72 | ~$0.85 | 15% |

---

## Routing Pause Protocol (smart pausing for cache efficiency)

### ROUTING CHECK — mandatory pause rule

When you see `⚠️ ROUTING CHECK` in your context, you MUST:
1. Show ONLY the routing options to the user
2. Wait for their reply
3. Do NOT answer the original question until they choose

This applies whether the check recommends upgrading OR downgrading the model.

---

### When Claude proceeds immediately (no pause):

**Model matches recommendation** — annotation says "Proceeding immediately".

**Implementation tasks** — pinning the model upfront prevents cache misses later.

- Tier 2: implement, add, create, fix, write, generate, build, refactor, optimize, debug, migrate, integrate, extend, update
- Tier 3: architect, design system, distributed system, microservice, infrastructure, refactor entire, overhaul, redesign, novel algorithm, from scratch

Example:
```
User: "add button to GenericTile control"

[ROUTING: Tier 2 — implementation/code task — sonnet]
Recommended model: `sonnet`. Pin this model for the entire task to maximize cache reuse.
Run `/model sonnet` to switch, then re-send. Or reply **continue** to pin current model for all subsequent turns.
```

Claude stops here. Waits for user to:
- Run `/model sonnet` + re-send prompt → switches and pins sonnet
- Reply **continue** → pins current model, proceeds with task
- Correct tier → override inline

Once user chooses: entire task runs on pinned model, cache accumulates unbroken.

---

## Session Boundaries (when tier resets)

New task = new session = re-classify tier.

```
Session 1: "add button to tile" → pin sonnet → 10 turns
  Cache: sonnet, full context by turn 10

Session 2: "what's the diff between tiles?" → Tier 1 exploration → haiku, no pause
  Cache: fresh start, haiku (different session)

Session 3: "build a tile dashboard" → pin opus → 15 turns
  Cache: fresh start, opus (new architecture task)
```

Each session starts with a clean tier decision. Old cache is gone, but sessions are consciously separated.

---

## Cost Comparison: Efficient vs Naive Routing

**Naive routing (switch mid-task):**
```
Turn 1–3 (haiku, clarification): $0.045
Switch to sonnet:
  Turn 4: context re-billed at sonnet = $0.008 (cache miss penalty)
Turn 5–10 (sonnet, implementation): $0.072
Total: $0.125
```

**Efficient routing (pin upfront):**
```
Decide: implementation expected, pin sonnet
Turn 1–3 (sonnet, clarification, full cache): $0.045
Turn 4–10 (sonnet, implementation, cache reuse 90%): $0.063
Total: $0.108
Savings: 13% ($0.017)
```

On a 50k-token context over 20 turns, pinning saves ~$0.13.

---

## Mode 3: Deactivation Flow

**Trigger:** "stop routing" · "/route-llm off" · natural-language deactivation

Run the deactivation script:
```bash
bash skills/route-llm/scripts/deactivate.sh
```

Confirm: "Routing mode deactivated."

---

## Mode 3: Deactivation Flow

**Trigger:** "stop routing" · "/route-llm off" · natural-language deactivation

Run the deactivation script:
```bash
bash skills/route-llm/scripts/deactivate.sh
```

Confirm: "Routing mode deactivated."
