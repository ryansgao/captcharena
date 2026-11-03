# Stage 1: build the static site with Zola (single binary, https://www.getzola.org). Fails on any broken internal link.
FROM ghcr.io/getzola/zola:v0.23.6 AS build
COPY site /site
WORKDIR /site
RUN ["/zola", "build", "--output-dir", "/tmp/public"]

# Stage 2: serve it with nginx running as a non-root user (nginx's own unprivileged image).
FROM nginxinc/nginx-unprivileged:1.31.7-alpine3.24
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /tmp/public /usr/share/nginx/html
# Zola skips hidden folders in static/, so security.txt is copied separately.
COPY site/static/.well-known /usr/share/nginx/html/.well-known
EXPOSE 8080
