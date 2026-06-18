#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py create_elasticsearch_indexes
python manage.py collectstatic --noinput

exec gunicorn --bind 0.0.0.0:8008 --workers "${GUNICORN_WORKERS:-3}" CentralManagement.wsgi
