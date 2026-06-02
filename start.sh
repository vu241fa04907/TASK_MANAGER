#!/bin/sh

python manage.py migrate --noinput
python manage.py collectstatic --noinput

gunicorn task_manager.wsgi:application --bind 0.0.0.0:$PORT