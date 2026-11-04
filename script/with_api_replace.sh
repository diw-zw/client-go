#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${0}")/.." && pwd)"
GO_BIN="${GO:-go}"
API_SOURCE="${1:-$ROOT/../rbg-api}"

if [[ $# -gt 0 ]]; then
    shift
fi

if [[ "${1:-}" != "--" ]]; then
    echo "usage: $0 [rbg-api-path] -- go-command..." >&2
    exit 2
fi
shift

if [[ $# -eq 0 ]]; then
    echo "error: no Go command supplied" >&2
    exit 2
fi

if [[ ! -f "$API_SOURCE/go.mod" ]]; then
    echo "error: rbg-api checkout not found at $API_SOURCE" >&2
    exit 2
fi

API_SOURCE="$(cd "$API_SOURCE" && pwd)"
BACKUP="$(mktemp)"
cp "$ROOT/go.mod" "$BACKUP"

cleanup() {
    if [[ "${KEEP_GO_MOD:-0}" == "1" ]]; then
        "$GO_BIN" mod edit "-dropreplace=sigs.k8s.io/rbgs/api"
        rm -f "$BACKUP"
    else
        mv "$BACKUP" "$ROOT/go.mod"
    fi
}
trap cleanup EXIT

cd "$ROOT"
"$GO_BIN" mod edit "-replace=sigs.k8s.io/rbgs/api=$API_SOURCE"

set +e
"$@"
status=$?
set -e

exit "$status"
