#!/usr/bin/env python3
"""
route-llm-hook.py — UserPromptSubmit hook for routing mode.
Provider-agnostic: auto-detects (Anthropic, OpenAI, Ollama, Azure).
Models discovered from provider API, no hardcoded IDs.
Tier classification via name heuristics (mini/nano → Tier 1, opus/70b → Tier 3, etc).
"""
import sys
import json
import re
import os
import urllib.request
import urllib.error
import pathlib
import datetime

FLAG = os.path.expanduser("~/.claude/.route-llm-active")
if not os.path.exists(FLAG):
    sys.exit(0)

try:
    payload = json.load(sys.stdin)
    prompt = payload.get("prompt", "")
except Exception:
    sys.exit(0)

if "<scheduled-task>" in prompt or "SYSTEM NOTIFICATION" in prompt:
    sys.exit(0)


def detect_provider():
    """Detect LLM provider from env vars. Order: explicit > Anthropic > OpenAI > Azure > Ollama > unknown."""
    if os.environ.get("ROUTE_LLM_PROVIDER"):
        return os.environ["ROUTE_LLM_PROVIDER"]

    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return "anthropic"

    if os.environ.get("OPENAI_API_KEY"):
        return "openai"

    if os.environ.get("AZURE_OPENAI_API_KEY"):
        return "azure"

    # Try Ollama local
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1)
        return "ollama"
    except Exception:
        pass

    return "unknown"


def discover_models(provider):
    """Query provider API for available models. Returns list of model IDs or empty list."""
    try:
        if provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                return []
            req = urllib.request.Request(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                return [m["id"] for m in data.get("data", [])]

        elif provider == "ollama":
            with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as resp:
                data = json.loads(resp.read())
                return [m["name"] for m in data.get("models", [])]

        elif provider == "azure":
            endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
            api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
            if not endpoint or not api_key:
                return []
            req = urllib.request.Request(
                f"{endpoint}/openai/deployments?api-version=2023-05-15",
                headers={"api-key": api_key}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                return [d["id"] for d in data.get("data", [])]

        elif provider == "anthropic":
            # Anthropic has no public /v1/models endpoint. Return empty — we'll use heuristics.
            return []

    except Exception:
        pass

    return []


def classify_model_tier(model_id):
    """Classify a model into tier 1/2/3 based on name heuristics."""
    name = str(model_id).lower()

    # Tier 1: small/cheap indicators
    tier1_keywords = ["mini", "nano", "small", "lite", "flash", "haiku", "micro",
                      "3b", "7b", "8b", "13b", "base", "edge"]
    if any(kw in name for kw in tier1_keywords):
        return 1

    # Tier 3: large/frontier indicators
    tier3_keywords = ["opus", "large", "heavy", "pro", "frontier", "max",
                      "70b", "405b", "turbo", "o1", "o3", "preview", "ultra", "advanced"]
    if any(kw in name for kw in tier3_keywords):
        return 3

    # Tier 2: default mid-tier
    return 2


def build_tier_models(models, provider):
    """Pick the best representative model for each tier from discovered list."""
    tier_models = {}
    for model_id in models:
        tier = classify_model_tier(model_id)
        if tier not in tier_models:
            tier_models[tier] = model_id

    # Provider-specific defaults if no models discovered
    defaults = {
        "anthropic": {1: "haiku", 2: "sonnet", 3: "opus"},
        "openai": {1: "gpt-4o-mini", 2: "gpt-4o", 3: "o1"},
        "ollama": {1: "mistral", 2: "neural-chat", 3: "llama3"},
    }

    default_set = defaults.get(provider, {})
    if 1 not in tier_models:
        tier_models[1] = default_set.get(1, "small-model")
    if 2 not in tier_models:
        tier_models[2] = default_set.get(2, "mid-model")
    if 3 not in tier_models:
        tier_models[3] = default_set.get(3, "large-model")

    return tier_models


def load_or_build_config(provider):
    """Load config from cache or discover and build. Returns config dict."""
    cache_dir = pathlib.Path.home() / ".route-llm"
    cache_file = cache_dir / "config.json"

    # Try load cache (if < 7 days old)
    if cache_file.exists():
        try:
            with open(cache_file) as f:
                config = json.load(f)
                if config.get("provider") == provider:
                    discovered_at = datetime.datetime.fromisoformat(config.get("discovered_at", ""))
                    age = datetime.datetime.now() - discovered_at
                    if age.days < 7:
                        return config  # Cache hit
        except Exception:
            pass

    # Build config from discovery
    models = discover_models(provider)
    tier_models = build_tier_models(models, provider)

    # Build tier_patterns (substrings that identify each tier in active model name)
    tier_patterns = {}
    for tier, model_id in tier_models.items():
        parts = str(model_id).lower().split(":")  # e.g., llama3:70b → [llama3, 70b]
        tier_patterns[tier] = parts

    # Determine API format and switch command
    api_format = "anthropic" if provider == "anthropic" else "openai"
    switch_cmd = "/model {model}" if provider == "anthropic" else None

    config = {
        "provider": provider,
        "discovered_at": datetime.datetime.now().isoformat(),
        "tier_models": {str(k): v for k, v in tier_models.items()},
        "tier_patterns": {str(k): v for k, v in tier_patterns.items()},
        "api_format": api_format,
        "switch_cmd": switch_cmd,
    }

    # Save cache
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

    return config


def classify_with_llm(prompt_text, config):
    """Call judge model via appropriate API format (Anthropic or OpenAI-compatible)."""
    api_format = config.get("api_format", "anthropic")

    # Determine credentials
    if api_format == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        base_url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com")
        judge_model = os.environ.get("OPENAI_LLM_JUDGE_MODEL", "gpt-4o-mini")
        if not api_key:
            return None, None
    elif config.get("provider") == "ollama":
        api_key = ""
        base_url = "http://localhost:11434"
        judge_model = config.get("tier_models", {}).get("1", "mistral")
    else:  # anthropic
        api_key = (os.environ.get("ANTHROPIC_API_KEY") or
                   os.environ.get("ANTHROPIC_AUTH_TOKEN", ""))
        base_url = (os.environ.get("ANTHROPIC_BASE_URL", "")).rstrip("/") or "https://api.anthropic.com"
        judge_model = os.environ.get("ANTHROPIC_DEFAULT_HAIKU_MODEL", "claude-haiku-4-5-20251001")
        if not api_key:
            return None, None

    system_prompt = (
        "What type of OUTPUT does this query require? Reply ONLY with 1, 2, or 3.\n\n"
        "1 = prose/text — email, message, explanation, summary, question answer, document\n"
        "2 = code/tests — source code, function, bug fix, unit test, code review\n"
        "3 = design — CREATE or DESIGN a new system/architecture/tech spec from scratch\n\n"
        "Key rule: classify by output type, not topic.\n"
        "'draft email about X' = 1. 'write code for X' = 2. 'design system for X' = 3."
    )

    try:
        if api_format == "openai":
            endpoint = f"{base_url}/v1/chat/completions"
            body = json.dumps({
                "model": judge_model,
                "max_tokens": 5,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_text[:3000]}
                ]
            }).encode()
            headers = {"content-type": "application/json", "Authorization": f"Bearer {api_key}"}
            req = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read())
                result = data["choices"][0]["message"]["content"].strip()
                digit = re.search(r"[123]", result)
                if digit and digit.group() in ("1", "2", "3"):
                    return int(digit.group()), "llm"

        else:  # anthropic (and ollama uses anthropic format)
            endpoint = f"{base_url}/v1/messages"
            body = json.dumps({
                "model": judge_model,
                "max_tokens": 5,
                "system": system_prompt,
                "messages": [{"role": "user", "content": prompt_text[:3000]}]
            }).encode()
            headers = {"anthropic-version": "2023-06-01", "content-type": "application/json"}
            if api_key:
                if os.environ.get("ANTHROPIC_API_KEY"):
                    headers["x-api-key"] = api_key
                else:
                    headers["Authorization"] = f"Bearer {api_key}"
            req = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read())
                result = data["content"][0]["text"].strip()
                digit = re.search(r"[123]", result)
                if digit and digit.group() in ("1", "2", "3"):
                    return int(digit.group()), "llm"
    except Exception:
        pass

    return None, None


def classify_with_regex(prompt_text):
    """Regex fallback classifier."""
    TIER3 = re.compile(
        r"\b(architect|design\s+system|distributed|microservice|infrastructure"
        r"|complex\s+system|refactor\s+entire|overhaul|redesign|novel\s+algorithm|from\s+scratch)\b",
        re.I,
    )
    TIER2 = re.compile(
        r"\b(implement|add\s+\w+|create\s+\w+|fix\s+bug|fix\s+\w+|write\s+test"
        r"|generate\s+code|build\s+\w+|refactor|optimize|debug|analyze|review|migrate|integrate)\b",
        re.I,
    )
    QUESTIONS = re.compile(
        r"^\s*(what|how|why|is|does|can|show|list|check|explain|find|search|describe)",
        re.I,
    )

    if TIER3.search(prompt_text):
        return 3, "regex"
    if TIER2.search(prompt_text):
        return 2, "regex"
    if QUESTIONS.match(prompt_text.strip()):
        return 1, "regex"
    return 1, "regex"


def active_model_tier(config):
    """Detect active model tier from env var (provider-specific)."""
    provider = config.get("provider")

    active_model_env_map = {
        "anthropic": "ANTHROPIC_MODEL",
        "openai": "OPENAI_MODEL",
        "azure": "AZURE_OPENAI_DEPLOYMENT",
        "ollama": None,
    }

    env_var = active_model_env_map.get(provider)
    if not env_var:
        return 1  # unknown or no env var → assume cheapest

    model_env = os.environ.get(env_var, "").lower()
    if not model_env:
        return 1

    # Check tier patterns
    tier_patterns = config.get("tier_patterns", {})
    for tier_str in ["3", "2"]:
        patterns = tier_patterns.get(tier_str, [])
        for p in patterns:
            if p and p in model_env:
                return int(tier_str)

    return 1


# Main routing logic
provider = detect_provider()
config = load_or_build_config(provider)

tier, source = classify_with_llm(prompt, config)
if tier is None:
    tier, source = classify_with_regex(prompt)

TIER_META = {
    1: (config.get("tier_models", {}).get("1", "small-model"), "quick", "lookup/question"),
    2: (config.get("tier_models", {}).get("2", "mid-model"), "code", "implementation/code task"),
    3: (config.get("tier_models", {}).get("3", "large-model"), "complex", "architecture/complex reasoning"),
}

model, label, reason = TIER_META[tier]
current_tier = active_model_tier(config)
current_model = os.environ.get("ANTHROPIC_MODEL") or os.environ.get("OPENAI_MODEL") or "unknown"
switch_cmd = config.get("switch_cmd")

if current_tier == tier:
    print(json.dumps({
        "systemMessage": (
            f"[ROUTING: {label} — {reason} — {model} — via {source}]\n"
            f"Proceeding immediately with {model}."
        )
    }))
elif current_tier < tier:
    msg = f"⚠️ ROUTING CHECK — respond to THIS before answering:\n[{label} — {reason} — via {source}]\n"
    msg += f"Current model `{current_model}` is weaker than recommended `{model}`.\n\n"
    msg += "Present ONLY these options to the user:\n"
    if switch_cmd:
        cmd = switch_cmd.format(model=model)
        msg += f"  A) `{cmd}` then re-send (switch up)\n"
    else:
        msg += f"  A) Switch to `{model}` in your tool, then re-send\n"
    msg += "  B) Reply `continue` to proceed on current model\n"
    msg += "\nDo NOT answer the original question yet."
    print(json.dumps({"systemMessage": msg}))
else:
    msg = f"⚠️ ROUTING CHECK — respond to THIS before answering:\n[{label} — {reason} — via {source}]\n"
    msg += f"Current model `{current_model}` is heavier than needed — `{model}` is sufficient.\n\n"
    msg += "Present ONLY these options to the user:\n"
    if switch_cmd:
        cmd = switch_cmd.format(model=model)
        msg += f"  A) `{cmd}` then re-send (cheaper)\n"
    else:
        msg += f"  A) Switch to `{model}` in your tool, then re-send\n"
    msg += "  B) Reply `continue` to proceed on current model\n"
    msg += "\nDo NOT answer the original question yet."
    print(json.dumps({"systemMessage": msg}))
