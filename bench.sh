#!/usr/bin/env bash
set -e
models=(jenny jenny-lite jenny-fast)
prompts=(
  "Say hi to Magdy in one short sentence."
  "Give Magdy 3 quick lunch ideas."
  "Tell a playful 5-sentence story about a lost tennis ball."
)
for m in "${models[@]}"; do
  if ! ollama show "$m" >/dev/null 2>&1; then
    echo "=== $m (not found, skipping) ==="
    continue
  fi
  echo "=== $m ==="
  # warmup (avoid cold-start penalty)
  ollama run "$m" "warmup" >/dev/null 2>&1 || true
  for p in "${prompts[@]}"; do
    echo "-- $p"
    /usr/bin/time -f "real %Es user %Us sys %Ss" ollama run "$m" "$p" >/dev/null
  done
  echo
done
