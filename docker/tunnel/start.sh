#!/bin/sh
set -eu
: "${VAST_SSH_HOST:?Set VAST_SSH_HOST in the Ansible-managed stack.env}"
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
test -s /run/secrets/vast_key
test -s /run/secrets/known_hosts
exec ssh -F /dev/null -N -T \
  -o BatchMode=yes -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile=/run/secrets/known_hosts \
  -o GlobalKnownHostsFile=/dev/null \
  -o ExitOnForwardFailure=yes -o ConnectTimeout=15 \
  -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
  -i /run/secrets/vast_key -p "$VAST_SSH_PORT" \
  -L 127.0.0.1:11434:127.0.0.1:11434 \
  "$VAST_SSH_USER@$VAST_SSH_HOST"
