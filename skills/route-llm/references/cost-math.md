# Cost Math

## Reference Pricing (September 2026 — verify current prices before quoting)

| Model | Input ($/M tokens) | Cached Input ($/M) | Output ($/M) |
|-------|-------------------|-------------------|--------------|
| haiku (Tier 1) | ~$0.10 | ~$0.01 | ~$0.25 |
| sonnet (Tier 2) | ~$0.80 | ~$0.08 | ~$2.40 |
| opus (Tier 3) | ~$5.00 | ~$0.50 | ~$15.00 |

Always check current prices at https://www.anthropic.com/pricing before quoting exact numbers to users.

---

## Blended Rate Formula

Given a traffic split across tiers:

```
blended_rate = (% Tier1 × haiku_price) + (% Tier2 × sonnet_price) + (% Tier3 × opus_price)
```

**Example — coding agent (70% Tier1/2, 30% Tier3):**
```
= (0.50 × 0.10) + (0.20 × 0.80) + (0.30 × 5.00)
= 0.05 + 0.16 + 1.50
= $1.71/M  vs  $5.00/M single-model opus  (66% reduction)
```

**Minimum useful example (80/20 split):**
```
= (0.80 × 0.10) + (0.20 × 5.00)
= 0.08 + 1.00
= $1.08/M  (78% reduction vs single opus)
```

---

## Session Pinning: Cache Math

In a multi-turn agent loop, input tokens compound. By turn 10 of a coding session, ~90% of input tokens are prior conversation history the model already processed.

**With prefix caching active (same model, same prefix):**
- Repeated tokens bill at ~10% of normal input rate
- A 50k-token history → 45k tokens at $0.05/M (cached) + 5k new at $0.50/M (sonnet)
- Without cache: 50k tokens at $0.50/M → ~10× more expensive

**When you switch models mid-session:**
- New model has no cached state for this conversation
- ALL tokens recomputed at full price every turn
- A 15-turn session where 90% of input is prefix → switching models costs ~9× more on input vs staying pinned

**Session pinning rule:** Make the routing decision ONCE at session start. Pin all subsequent requests in that session to the same model. Most providers implement this via a session or affinity ID header.

---

## RouteLLM Research Benchmark (ICLR 2025)

- Matrix-factorization router: 95% of GPT-4 quality on MT Bench
- Only 14% of queries needed the strong model → 85% cost reduction
- Routers generalized to model pairs they weren't trained on

**Uber case study (December 2025 → April 2026):**
- 5,000 engineers, all on frontier model (Claude Code)
- Entire annual AI budget exhausted in ~4 months
- Power users: $500–$2,000/month; one exec: $1,200 in a single 2-hour session
- Root cause: docstring lookups billed at the same rate as distributed systems refactors
