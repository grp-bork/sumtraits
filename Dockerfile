FROM python:3.11-alpine

# Bash is required for Nextflow task scripts; procps provides ps for tracing.
RUN apk add --no-cache bash git procps

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

RUN taxonomic-profile-translator install-data
RUN taxonomic-profile-translator check-data

