FROM python:3.13-slim AS build
ADD requirements.txt .
RUN python -m venv venv && \
    venv/bin/pip install --require-hashes -r requirements.txt --no-cache-dir
ARG EXTRA_LIBS=""
RUN if [ -n "$EXTRA_LIBS" ]; then \
  /venv/bin/pip install --no-cache-dir $EXTRA_LIBS; \
fi
RUN venv/bin/pip install opentelemetry-distro

RUN venv/bin/opentelemetry-bootstrap -a install

FROM python:3.13-slim
COPY --from=build /venv/ /venv/

WORKDIR /app
COPY pyproject.toml .
COPY garf garf

ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
ENV PYTHONPATH=/app

CMD ["/venv/bin/opentelemetry-instrument", "/venv/bin/uvicorn", "garf.executors.entrypoints.server:app", "--host", "0.0.0.0"]
