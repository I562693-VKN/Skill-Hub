#!/usr/bin/env bash
# deactivate.sh — remove flag file to disable routing mode

rm -f ~/.claude/.route-llm-active
echo "Routing mode deactivated."
