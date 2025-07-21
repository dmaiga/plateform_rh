#!/bin/sh

echo "Checking for missing migrations..."

# Crée les migrations seulement si besoin
python manage.py makemigrations --check --dry-run > /dev/null 2>&1

if [ $? -eq 1 ]; then
    echo "Generating new migrations..."
    python manage.py makemigrations
else
    echo "No new migrations needed."
fi

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting production server with Gunicorn..."
gunicorn antares_rh.wsgi:application --chdir . --bind 0.0.0.0:8000
