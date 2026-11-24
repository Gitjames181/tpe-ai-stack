#!/bin/sh
set -eu
# Invoked on every start by the Vast SSH template, including after a stop/start.
mkdir -p /workspace/models /workspace/tpe-ai /var/log/tpe-ai /etc/tpe-ai
if [ ! -f /etc/tpe-ai/worker.json ]; then
    cp /opt/tpe-ai/worker.example.json /etc/tpe-ai/worker.json
fi
chown 10001:10001 /workspace/models /workspace/tpe-ai /var/log/tpe-ai
python3 -c 'import sys; sys.path.insert(0, "/opt/tpe-ai"); from config import load_config; load_config()'
if [ "${1:-}" = "--foreground" ]; then
    exec supervisord -n -c /opt/tpe-ai/supervisord.conf
fi
if supervisorctl -c /opt/tpe-ai/supervisord.conf pid >/dev/null 2>&1; then
    supervisorctl -c /opt/tpe-ai/supervisord.conf status
else
    supervisord -c /opt/tpe-ai/supervisord.conf
fi
