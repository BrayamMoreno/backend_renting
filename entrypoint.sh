#!/usr/bin/env bash
set -e

echo "=== Esperando conexión a la Base de Datos MySQL (${DB_HOST:-db}:${DB_PORT:-3306}) ==="

while ! nc -z ${DB_HOST:-db} ${DB_PORT:-3306}; do
  sleep 1
done

echo "✓ Conexión a la base de datos MySQL establecida."

echo "1. Ejecutando migraciones..."
python manage.py migrate --noinput

echo "2. Ejecutando inicialización de BD, roles y superusuario (init_db)..."
python manage.py init_db

echo "3. Generando backup inicial de arranque..."
python manage.py backup_db --force || true

echo "=== Iniciando servidor WSGI Gunicorn ==="
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
