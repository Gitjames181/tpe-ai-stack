# Build and publish privately, then record the resulting registry digest.
ARG OLLAMA_IMAGE=ollama/ollama:0.40.18
FROM ${OLLAMA_IMAGE}
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 supervisor openssh-server ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 10001 tpe-ai \
    && useradd -m -u 10001 -g 10001 -s /usr/sbin/nologin tpe-ai
COPY vast/ /opt/tpe-ai/
RUN chmod 0555 /opt/tpe-ai/start.sh \
    && mkdir -p /etc/tpe-ai /workspace/models /workspace/tpe-ai /var/log/tpe-ai \
    && cp /opt/tpe-ai/worker.example.json /etc/tpe-ai/worker.json \
    && chown -R 10001:10001 /workspace/models /workspace/tpe-ai /var/log/tpe-ai
# Vast SSH launch mode replaces the inherited entrypoint.
# Required on-start command: /opt/tpe-ai/start.sh
ENTRYPOINT ["/opt/tpe-ai/start.sh"]
CMD ["--foreground"]
