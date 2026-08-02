FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml manage.py ./
COPY crowdsmarter ./crowdsmarter
COPY apps ./apps
RUN pip install --upgrade pip && pip install .

FROM base AS development
RUN pip install -e ".[dev]"
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS production
RUN python manage.py collectstatic --noinput
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/media \
    && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl --fail http://127.0.0.1:8000/health/live/ || exit 1
CMD ["gunicorn", "crowdsmarter.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "60", "--access-logfile", "-"]
