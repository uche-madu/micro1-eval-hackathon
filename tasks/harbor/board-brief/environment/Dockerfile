FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash curl ca-certificates git jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY data /data
RUN mkdir -p /output
