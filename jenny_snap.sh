#!/usr/bin/env bash
set -euo pipefail
SNAPDIR="$HOME/ai/jenny/.snapshots"
ROOT="$HOME"
SRC="$ROOT/ai/jenny"
mkdir -p "$SNAPDIR"

usage(){ cat <<USAGE
Usage:
  $0 save [label]                     # create snapshot of ~/ai/jenny (excludes .snapshots)
  $0 ls                               # list snapshots
  $0 restore <file|latest> [--keep-memory]  # restore snapshot
USAGE
}

now(){ date +%Y%m%d-%H%M%S; }

case "${1:-}" in
  save)
    LABEL="${2:-}"; TS="$(now)"
    BASE="jenny_${TS}${LABEL:+_$LABEL}.tar.gz"
    SNAP="$SNAPDIR/$BASE"
    pushd "$ROOT" >/dev/null
    tar --exclude='ai/jenny/.snapshots' -czf "$SNAP" ai/jenny
    popd >/dev/null
    sha256sum "$SNAP" > "$SNAP.sha256"
    printf "Saved: %s\n" "$SNAP"
    ;;
  ls)
    ls -lh "$SNAPDIR" 2>/dev/null || echo "No snapshots yet."
    ;;
  restore)
    TARGET="${2:-latest}"; KEEP_MEM="${3:-}"
    if [ "$TARGET" = "latest" ]; then
      SNAPFILE="$(ls -1t "$SNAPDIR"/jenny_*.tar.gz 2>/dev/null | head -n1 || true)"
      [ -n "$SNAPFILE" ] || { echo "No snapshots found."; exit 1; }
    else
      SNAPFILE="$TARGET"; [[ -f "$SNAPFILE" ]] || SNAPFILE="$SNAPDIR/$SNAPFILE"
      [ -f "$SNAPFILE" ] || { echo "Snapshot not found: $TARGET"; exit 1; }
    fi
    echo "Snapshot: $SNAPFILE"
    [ -f "$SNAPFILE.sha256" ] && sha256sum -c "$SNAPFILE.sha256" || true

    TMPMEM=""
    if [ "$KEEP_MEM" = "--keep-memory" ] && [ -d "$SRC/memory" ]; then
      TMPMEM="$(mktemp -d)"; cp -a "$SRC/memory" "$TMPMEM/"; echo "Preserved memory."
    fi

    [ -d "$SRC" ] && mv "$SRC" "${SRC}.bak.$(now)" || true
    pushd "$ROOT" >/dev/null; tar -xzf "$SNAPFILE"; popd >/dev/null

    if [ -n "${TMPMEM:-}" ] && [ -d "$TMPMEM/memory" ]; then
      rm -rf "$SRC/memory"; mv "$TMPMEM/memory" "$SRC/"; echo "Memory restored."
    fi
    echo "Restored: $SRC"
    ;;
  *) usage; exit 1;;
esac
