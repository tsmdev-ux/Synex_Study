#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

: "${GUNICORN_TIMEOUT:=120}"
: "${GUNICORN_GRACEFUL_TIMEOUT:=30}"
: "${GUNICORN_WORKERS:=2}"
: "${GUNICORN_KEEPALIVE:=5}"
: "${GUNICORN_LOG_LEVEL:=info}"

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "$GUNICORN_WORKERS" \
  --timeout "$GUNICORN_TIMEOUT" \
  --graceful-timeout "$GUNICORN_GRACEFUL_TIMEOUT" \
  --keep-alive "$GUNICORN_KEEPALIVE" \
  --access-logfile "-" \
  --error-logfile "-" \
  --log-level "$GUNICORN_LOG_LEVEL"
