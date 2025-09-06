#!/usr/bin/env bash
set -e
LABEL="${1:-manual}"
STAMP=$(date +%Y-%m-%d_%H:%M:%S)
MD="$HOME/ai/jenny/LOCKPOINT.md"
mkdir -p "$HOME/ai/jenny/.snapshots"
# save snapshot
"$HOME/ai/jenny/jenny_snap.sh" save "$LABEL" >/tmp/jenny_snap.out
SNAP=$(grep '^Saved:' /tmp/jenny_snap.out | awk '{print $2}')
# append manifest line
{
  echo "- $STAMP  |  SNAP: $(basename "$SNAP")  |  label: $LABEL  |  model: jenny:latest  |  chat_loop v1.2 | prompt_builder v1.1 | ollama 0.11.6"
} >> "$MD"
echo "Checkpoint recorded:"
tail -n 1 "$MD"
