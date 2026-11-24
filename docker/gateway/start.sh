#!/bin/sh
set -eu
case "${TPE_AI_API_KEY:-}" in
  ""|*[!a-zA-Z0-9_-]*) echo "Set TPE_AI_API_KEY to 32-128 URL-safe characters in Komodo" >&2; exit 2 ;;
esac
if [ "${#TPE_AI_API_KEY}" -lt 32 ] || [ "${#TPE_AI_API_KEY}" -gt 128 ]; then
  echo "TPE_AI_API_KEY must contain 32-128 characters" >&2; exit 2
fi
AI_RUN_DIR=${AI_RUN_DIR:-/run/ai}
umask 077
mkdir -p "$AI_RUN_DIR"
printf '"Bearer %s" tpe;\n' "$TPE_AI_API_KEY" > "$AI_RUN_DIR/tokens.conf"
unset TPE_AI_API_KEY
exec nginx -g 'daemon off;'
