# Yangi Samarqand — Django API (gunicorn)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
RUN useradd --create-home --uid 1000 app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh \
    && mkdir -p /data/media /app/staticfiles \
    && chown -R app:app /app /data
USER app

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
# sync workers + threads; generous timeout for large video uploads
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "4", "--timeout", "300", "--access-logfile", "-"]
