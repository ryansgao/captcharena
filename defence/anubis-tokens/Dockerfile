FROM golang:1.27-alpine AS build
ENV CGO_ENABLED=0 GOTOOLCHAIN=local
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY gate/ gate/
COPY cmd/ cmd/
RUN go build -trimpath -ldflags=-s -o /out/ppgate ./cmd/ppgate && go build -trimpath -ldflags=-s -o /out/ppclient ./cmd/ppclient

FROM alpine:3.22
RUN adduser -D -u 10001 gate && install -d -o gate -g gate /data
COPY --from=build /out/ /usr/local/bin/
COPY .deployed* /srv/
USER gate
EXPOSE 8080
CMD ["ppgate"]
