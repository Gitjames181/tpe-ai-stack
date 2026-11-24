#!/bin/sh
set -eu
: "${VAST_SSH_HOST:?Set VAST_SSH_HOST in the Komodo Stack environment}"
: "${VAST_SSH_PORT:?Set the mapped Vast SSH port}"
VAST_SSH_USER=${VAST_SSH_USER:-root}
case "$VAST_SSH_HOST" in
  -*|""|*[!a-zA-Z0-9.:-]*) echo "Invalid VAST_SSH_HOST" >&2; exit 2 ;;
esac
case "$VAST_SSH_USER" in
  -*|""|*[!a-zA-Z0-9_-]*) echo "Invalid VAST_SSH_USER" >&2; exit 2 ;;
esac
case "$VAST_SSH_PORT" in
  ""|*[!0-9]*) echo "Invalid VAST_SSH_PORT" >&2; exit 2 ;;
esac
[ "$VAST_SSH_PORT" -ge 1 ] && [ "$VAST_SSH_PORT" -le 65535 ] || exit 2
if [ -z "${VAST_SSH_PRIVATE_KEY_B64:-}" ] || [ -z "${VAST_SSH_KNOWN_HOSTS:-}" ]; then
  echo "Set the dedicated SSH key and verified known_hosts record in Komodo" >&2; exit 2
fi
AI_RUN_DIR=${AI_RUN_DIR:-/run/ai}
umask 077
mkdir -p "$AI_RUN_DIR"
if ! printf '%s' "$VAST_SSH_PRIVATE_KEY_B64" | base64 -d > "$AI_RUN_DIR/id_ed25519" 2>/dev/null; then
  echo "Invalid base64 SSH key" >&2; exit 2
fi
printf '%s\n' "$VAST_SSH_KNOWN_HOSTS" > "$AI_RUN_DIR/known_hosts"
unset VAST_SSH_PRIVATE_KEY_B64 VAST_SSH_KNOWN_HOSTS
if ! ssh-keygen -y -P '' -f "$AI_RUN_DIR/id_ed25519" >/dev/null 2>&1; then
  echo "The dedicated SSH key must be valid and usable without an interactive passphrase" >&2; exit 2
fi
key_host=$VAST_SSH_HOST
if [ "$VAST_SSH_PORT" -ne 22 ]; then key_host="[$VAST_SSH_HOST]:$VAST_SSH_PORT"; fi
if ! ssh-keygen -F "$key_host" -f "$AI_RUN_DIR/known_hosts" >/dev/null 2>&1; then
  echo "The verified known_hosts record does not match the selected SSH endpoint" >&2; exit 2
fi
exec ssh -F /dev/null -N -T \
  -o BatchMode=yes -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes \
  -o "UserKnownHostsFile=$AI_RUN_DIR/known_hosts" \
  -o GlobalKnownHostsFile=/dev/null \
  -o ExitOnForwardFailure=yes -o ConnectTimeout=15 \
  -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
  -i "$AI_RUN_DIR/id_ed25519" -p "$VAST_SSH_PORT" \
  -L 127.0.0.1:11434:127.0.0.1:11434 \
  "$VAST_SSH_USER@$VAST_SSH_HOST"
