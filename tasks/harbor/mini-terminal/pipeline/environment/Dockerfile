FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends bash curl ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY data /workspace/data
COPY pipeline.py /workspace/pipeline.py
RUN mkdir -p /workspace/out /output
