ARG ALPINE_IMAGE=alpine:3.24.4
FROM ${ALPINE_IMAGE}
RUN apk add --no-cache openssh-client \
    && addgroup -g 10001 ai \
    && adduser -D -u 10001 -G ai ai
COPY docker/tunnel/start.sh /usr/local/bin/start-tunnel
RUN chmod 0555 /usr/local/bin/start-tunnel
USER 10001:10001
ENTRYPOINT ["/usr/local/bin/start-tunnel"]
