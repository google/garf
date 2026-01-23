FROM python:3.11.8-alpine
COPY --from=ghcr.io/astral-sh/uv:0.5.18 /uv /bin/
ENV UV_SYSTEM_PYTHON=1
WORKDIR /app
ADD requirements.txt .
RUN uv pip install --require-hashes -r requirements.txt
ARG EXTRA_LIBS=""
RUN if [ -n "$EXTRA_LIBS" ]; then \
  uv pip install --no-cache-dir $EXTRA_LIBS; \
fi

ENTRYPOINT ["uvicorn", "garf_executors.entrypoints.server:app", "--host", "0.0.0.0"]
