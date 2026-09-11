# 🚀 route-llm: Intelligent LLM Model Routing

Automatic model tier classification and routing for multi-model LLM environments. **Zero configuration, multi-provider support, and dynamic model discovery.**

## ✨ What It Does

route-llm pre-classifies every prompt into tiers (Tier 1: cheap, Tier 2: mid, Tier 3: frontier) and recommends the optimal model for your task **before you write a single line of code**. Works with **any LLM provider** — Anthropic, OpenAI, Ollama, Azure — without a single hardcoded model ID.

```
User: "draft email about fiori elements"
        ↓
route-llm classifies as Tier 1 (prose output)
        ↓
Suggests: haiku / gpt-4o-mini / mistral (cheapest option)
        ↓
Proceeds immediately ✓ (no pause, instant)
```

```
User: "design a microservice architecture"
        ↓
route-llm classifies as Tier 3 (architecture design)
        ↓
Suggests: opus / o1 / llama3:70b (frontier model)
        ↓
Pauses and asks you to pin the model (cache efficiency) ⚠️
```

---

## 🎯 Why You Need This

### The Problem
- **Model mismatch = wasted money.** Using opus for a simple question, or haiku for complex reasoning.
- **Manual routing fatigue.** "Which model should I use?" every time.
- **Provider lock-in.** Switch from Claude to OpenAI to Ollama? Rewrite routing logic.
- **Cache misses.** Switching models mid-task destroys your 5-minute cache window (90% cost reduction lost).
- **Future fragility.** New models released? Code breaks.

### The Solution
route-llm **automates model selection** based on task type, works with any provider, adapts to new models automatically, and optimizes for cache reuse.

**Cost savings: 13–73% per session** (see [Session Pinning Strategy](#-session-pinning--cache-efficiency) below).

---

## 🌍 Multi-Provider Support

| Provider | Auto-Detect | Model Discovery | Model Switch |
|----------|:---:|:---:|:---:|
| **Anthropic** (Claude) | ✅ `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` | Name heuristics (`claude-*`) | `/model {name}` (CLI) |
| **OpenAI** (GPT-4, o1) | ✅ `OPENAI_API_KEY` | 🔍 Live API scan | Manual switch |
| **Ollama** (Local) | ✅ Port `localhost:11434` | 🔍 Live API scan | Manual switch |
| **Azure OpenAI** | ✅ `AZURE_OPENAI_API_KEY` | 🔍 Live API scan | Manual switch |
| **Custom / Unknown** | ❌ | Tier labels only | — |

**Zero configuration needed.** Just set your provider's API key and activate route-llm.

---

## 📦 Installation

### 1. Prerequisites
- Claude Code, Cline, Copilot, or any LLM IDE/tool
- Python 3.9+
- Your LLM provider API key(s) already in environment variables

### 2. Install
Clone or copy this skill into your project's skills directory:
```bash
git clone https://github.com/[your-repo]/ai-powered-support-assistant.git
cd ai-powered-support-assistant
```

### 3. Activate
Run the activation command in your tool:
```bash
/route-llm on
```

Or manually:
```bash
bash skills/route-llm/scripts/activate.sh
```

This registers the routing hook and creates the cache directory (`~/.route-llm`).

**Restart your tool** for the hook to take effect.

---

## 🚄 Quick Start

### Example 1: Simple Question (Tier 1 → Immediate)
```
You: "What is Fiori Elements?"

route-llm: [ROUTING: quick — lookup/question — haiku]
           Proceeding immediately with haiku.

→ Fast, cheap answer. No pause.
```

### Example 2: Code Task (Tier 2 → Pause & Pin)
```
You: "fix the authentication bug in this middleware"

route-llm: ⚠️ ROUTING CHECK
           [code — implementation/code task — sonnet]
           Current model is weaker than recommended.
           
           Pick one:
           A) /model sonnet (switch up)
           B) continue (stay on current model)

You: /model sonnet
     (then re-send your prompt)

→ Context pinned to sonnet for entire session.
  Cache stays warm, 13% cost savings.
```

### Example 3: Architecture Design (Tier 3 → Pause & Pin)
```
You: "architect a microservice system for real-time analytics"

route-llm: ⚠️ ROUTING CHECK
           [complex — architecture/complex reasoning — opus]
           Current model weaker than recommended.
           
           Pick one:
           A) /model opus (switch up)
           B) continue (stay on current model)

You: continue
     (or switch to opus if on a weaker model)

→ Tier 3 reasoning on frontier model.
  Cache efficiency maximized.
```

---

## 🔧 How It Works

### Step 1: Provider Detection
route-llm scans your environment variables (in order):
1. `ROUTE_LLM_PROVIDER` (explicit override, if set)
2. `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` → **Anthropic**
3. `OPENAI_API_KEY` → **OpenAI**
4. `AZURE_OPENAI_API_KEY` → **Azure**
5. `localhost:11434` port check → **Ollama** (local)
6. Default → **Unknown** (tier labels only)

### Step 2: Dynamic Model Discovery
On first activation (or every 7 days), route-llm queries your provider's model API:
- **OpenAI**: `GET /v1/models` → lists gpt-4o, gpt-4o-mini, o1, ...
- **Ollama**: `GET /api/tags` → lists mistral, llama3:70b, codellama, ...
- **Anthropic**: Uses name heuristics (no public API)
- **Azure**: `GET /deployments` → lists your custom deployments

### Step 3: Intelligent Tier Classification
Each discovered model is auto-classified into Tier 1/2/3 via **name heuristics** (no hardcoded IDs):

| Keyword Pattern | Tier | Examples |
|---|:---:|---|
| `mini`, `nano`, `7b`, `8b`, `flash`, `haiku` | **1** | gpt-4o-mini, mistral:7b |
| (default) | **2** | gpt-4o, codellama, sonnet |
| `70b`, `405b`, `opus`, `o1`, `turbo`, `frontier` | **3** | llama3:70b, o1, opus |

**New models automatically classified.** No code changes needed when OpenAI releases GPT-5o or Ollama adds a new model.

### Step 4: Prompt Classification
When you send a prompt, route-llm classifies it into a tier:
- **Tier 1**: Prose output (questions, emails, summaries, explanations)
- **Tier 2**: Code output (bug fixes, tests, implementations, reviews)
- **Tier 3**: Design output (architecture, system design, novel algorithms)

Classification uses:
1. **LLM judge** (haiku/gpt-4o-mini): "What type of output does this query require?" → 1, 2, or 3
2. **Regex fallback**: Keyword matching (architecture → 3, fix bug → 2, what/why/how → 1)

### Step 5: Routing Decision
Compare **recommended tier** vs **current model tier**:

| Case | Action |
|------|--------|
| Match | ✓ Proceed immediately (annotate routing) |
| Current weaker | ⚠️ Pause & ask to upgrade |
| Current stronger | ⚠️ Pause & offer to downgrade (save cost) |

### Step 6: Caching
Config is cached at `~/.route-llm/config.json` (machine-level, not per-project):
```json
{
  "provider": "openai",
  "discovered_at": "2026-09-11T10:00:00",
  "tier_models": {"1": "gpt-4o-mini", "2": "gpt-4o", "3": "o1"},
  "tier_patterns": {"1": ["mini"], "2": ["gpt-4"], "3": ["o1", "turbo"]},
  "api_format": "openai",
  "switch_cmd": null
}
```

Cache invalidates after **7 days** → auto-rediscovers (models may be retired, new ones released).

---

## 💰 Session Pinning & Cache Efficiency

### Problem: Model Switching Breaks Cache
Every time you switch models mid-conversation, the full context gets re-billed at the new model's rates:

```
Turn 1–3 (haiku, clarification)  : $0.045
Switch to sonnet:
  Turn 4 (cache miss)             : $0.008 ← full re-billing
Turn 5–10 (sonnet, implementation): $0.072
Total: $0.125 ❌
```

### Solution: Pin the Model for the Session
route-llm recommends you pin the optimal model **upfront**, keep it throughout the session:

```
Pin sonnet (Tier 2) upfront
Turn 1–3 (sonnet, full cache)     : $0.045
Turn 4–10 (sonnet, 90% cached)    : $0.063
Total: $0.108 ✅ (13% savings!)
```

### Cost Savings by Scenario
| Scenario | Pin Model | Switch Mid-Task | Savings |
|----------|:---:|:---:|:---:|
| Clarify → implement (7k context, 10 turns) | $0.108 | $0.125 | **13%** |
| Pure exploration (7k context, 5 turns) | $0.012 | $0.045 | **73%** |
| Large context (50k tokens, 20 turns) | $0.72 | $0.85 | **15%** |

route-llm's **pause & pin strategy** automatically captures these savings.

---

## 🎮 Usage Guide

### Commands

#### Activate routing (always-on mode)
```bash
/route-llm on
```
Registers the hook. Routing happens automatically on every prompt from now on.

#### Deactivate routing
```bash
/route-llm off
# or
stop routing
```
Removes the hook. Prompts proceed without routing classification.

#### One-shot analysis (no always-on)
```bash
/route-llm [task description]
```
Classifies a single workload into tasks, maps each to tiers, calculates blended cost, and recommends session pinning.

Example:
```bash
/route-llm extract 50 SNOW tickets, analyze each with Fiori Elements V4 debugger, generate RCA report
```

Returns:
```
## Task Classification
| Task | Tier | Rationale |
|------|------|-----------|
| Extract tickets | 1 | Lookup/extraction |
| Analyze with V4 debugger | 3 | Forensic analysis, multi-step investigation |
| Generate RCA report | 2 | Code review / documentation |

## Routing Table
| Task | Tier | Model | Notes |
|------|------|-------|-------|
| Extract tickets | 1 | gpt-4o-mini | Fast, cheap |
| Analyze with V4 debugger | 3 | o1 | Frontier reasoning needed |
| Generate RCA report | 2 | gpt-4o | Mid-tier, good output quality |

## Session Pinning
Required — Tasks 2 and 3 both need o1; pinning saves cache invalidation penalty.

## Cost Estimate
Blended: ~$0.45/M tokens vs single-model (all o1) ~$0.52/M (~13% reduction)
```

---

## 🔨 Configuration

### Environment Variables

**Override provider detection:**
```bash
export ROUTE_LLM_PROVIDER=openai  # Force OpenAI (ignore Anthropic key if present)
```

**Cache location:**
```bash
# Default: ~/.route-llm/config.json
# Machine-level, not per-project. Persists across tool restarts.
```

**Active model (provider-specific):**
```bash
export ANTHROPIC_MODEL=opus          # Claude Code sets this
export OPENAI_MODEL=gpt-4o           # If using OpenAI
export AZURE_OPENAI_DEPLOYMENT=gpt4  # If using Azure
```

---

## 📊 Examples

### Example: Anthropic + Claude Code (Default)
```bash
# Environment
export ANTHROPIC_AUTH_TOKEN=sk-ant-...
export ANTHROPIC_BASE_URL=http://localhost:6655/anthropic/

# Activate
/route-llm on

# Use
You: "draft an email explaining Fiori Elements"
route-llm: [ROUTING: quick — lookup/question — haiku]
           Proceeding immediately.

You: /model sonnet
     fix the OData binding issue in sap.fe.templates

route-llm: ⚠️ ROUTING CHECK
           Current model weaker. Recommend sonnet.
           A) /model sonnet
           B) continue
```

### Example: OpenAI + Cline
```bash
# Environment
export OPENAI_API_KEY=sk-proj-...

# Activate
/route-llm on

# route-llm auto-detects OpenAI, discovers [gpt-4o-mini, gpt-4o, o1]

You: "review this pull request for security bugs"
route-llm: [ROUTING: code — implementation/code task — gpt-4o]
           Switch to gpt-4o in your tool, then re-send.
           Or reply continue to proceed on current model.
```

### Example: Ollama Local
```bash
# Environment
# (no API key needed, port check works)

# Activate
/route-llm on

# route-llm auto-detects localhost:11434, discovers [mistral, codellama:34b, llama3:70b]

You: "design a distributed caching layer"
route-llm: ⚠️ ROUTING CHECK
           [complex — architecture/complex reasoning]
           Recommended: llama3:70b (largest local model).
           Switch in your Ollama client, then reply continue.
```

---

## 🐛 Troubleshooting

### Hook doesn't fire
**Problem:** You activate route-llm but don't see routing annotations.

**Solution:**
1. Restart your tool (hook registration requires tool restart)
2. Check hook registered: `grep -i route-llm ~/.claude/settings.json`
3. Verify flag file exists: `ls ~/.claude/.route-llm-active`

### "Unknown provider" tier labels showing
**Problem:** Models show as "small-model", "mid-model", "large-model" (no actual names).

**Solution:**
1. Set your provider API key in env vars (OpenAI: `OPENAI_API_KEY`, Anthropic: `ANTHROPIC_API_KEY`)
2. Clear cache: `rm ~/.route-llm/config.json`
3. Re-activate: `/route-llm on`

### Cache out of sync
**Problem:** New models not being discovered, or old retired models still showing.

**Solution:**
```bash
rm ~/.route-llm/config.json
# Next prompt will rediscover all models
```

### API errors
**Problem:** "Connection timeout" or "401 Unauthorized"

**Check:**
- API key is valid and not expired: `echo $OPENAI_API_KEY` (or your provider's var)
- Internet connection working
- Provider API endpoint is reachable (`curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`)

---

## 📖 Learn More

- [Tier Classification Taxonomy](references/routing-taxonomy.md) — Detailed tier definitions
- [Cost Math & Cache Efficiency](references/cost-math.md) — Blended cost calculations
- [Routing Pause Protocol](SKILL.md) — How routing decisions are made

---

## 📝 License

Apache 2.0

---

## 🤝 Contributing

Found a bug? Have a feature idea? Open an issue or PR!

Current limitations & planned:
- [ ] Real-time model performance tracking (cost/latency per tier)
- [ ] Custom tier heuristics per user/org
- [ ] Multi-provider cost comparison dashboard
- [ ] Integration with LLM observability tools (Langfuse, LLMonitor, etc)

---

## 💡 FAQ

**Q: Do I need to pay for route-llm?**
A: No, it's free and open-source. You pay only for the LLM calls themselves (via your provider's API).

**Q: Does route-llm work offline?**
A: Yes, for Ollama (fully local). For OpenAI/Anthropic/Azure, you need internet to reach the provider.

**Q: Can I force a specific model?**
A: Yes, reply `continue` when route-llm pauses, or set `ROUTE_LLM_PROVIDER=<name>` to override.

**Q: What if my provider isn't listed?**
A: Set `ROUTE_LLM_PROVIDER=unknown` and route-llm will use tier labels only (no model names). Open an issue and we'll add support.

**Q: Does route-llm send my prompts anywhere?**
A: No. The hook runs locally. Only the haiku/gpt-4o-mini LLM judge (for tier classification) is called via your provider's API, and only if the hook is active. Your prompts stay in your tool.

**Q: Can I use route-llm with multiple providers?**
A: Not simultaneously. Set one provider via env vars. To switch, update env vars and clear cache (`rm ~/.route-llm/config.json`).

---

**Made with ❤️ for multi-model LLM workflows.**
