FROM python:3.11-alpine

ENV TAXONKIT_DB="/ncbi_data/"
ENV TPT_DB_PATH="/tpt_data/"

# Bash is required for Nextflow task scripts; procps provides ps for tracing.
RUN apk add --no-cache bash git procps

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

RUN tpt install
RUN tpt verify
