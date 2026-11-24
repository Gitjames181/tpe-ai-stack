ARG NGINX_IMAGE=nginx:1.30.8-alpine
FROM ${NGINX_IMAGE}
COPY docker/gateway/nginx.conf /etc/nginx/nginx.conf
COPY docker/gateway/proxy.conf /etc/nginx/ai-proxy.conf
USER 101:101
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
