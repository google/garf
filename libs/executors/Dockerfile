FROM python:3.11.8-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:0.5.18 /uv /bin/
ENV UV_SYSTEM_PYTHON=1
WORKDIR /app
ADD requirements.txt .
RUN uv pip install --require-hashes -r requirements.txt --target /install

FROM python:3.11.8-alpine AS final
WORKDIR /app
COPY --from=builder /install /usr/local/lib/python3.11/site-packages/
COPY --from=builder /install/bin/ /usr/local/bin/
ENTRYPOINT ["uvicorn", "garf_executors.entrypoints.server:app", "--host", "0.0.0.0"]
