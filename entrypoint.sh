#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until python -c "
import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('db', 5432))
    s.close()
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "   PostgreSQL not ready — retrying in 2 s..."
    sleep 2
done
echo "PostgreSQL is ready!"

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn sfabc.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120
