#!/usr/bin/env bash
# activate.sh — register route-llm hook and write flag file

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOOK_SCRIPT="$SCRIPT_DIR/hooks/route-llm-hook.py"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SETTINGS_FILE="$PROJECT_ROOT/.claude/settings.json"

chmod +x "$HOOK_SCRIPT"
mkdir -p "$PROJECT_ROOT/.claude"

python3 - <<PYEOF
import json, os, sys

settings_file = "$SETTINGS_FILE"
hook_script = "$HOOK_SCRIPT"

try:
    with open(settings_file) as f:
        settings = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    settings = {}

hooks = settings.setdefault("hooks", {})
uph = hooks.setdefault("UserPromptSubmit", [])

# Idempotent — skip if already registered
for entry in uph:
    for h in entry.get("hooks", []):
        if h.get("command") == hook_script:
            print("Hook already registered.")
            sys.exit(0)

uph.append({"hooks": [{"type": "command", "command": hook_script, "timeout": 8}]})

with open(settings_file, "w") as f:
    json.dump(settings, f, indent=2)

print(f"Hook registered: {hook_script}")
PYEOF

touch ~/.claude/.route-llm-active
mkdir -p ~/.route-llm

echo "Routing mode active."
