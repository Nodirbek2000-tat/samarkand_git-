#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput --verbosity 0
# first deploy only: Uzbek starter content + the first administrator from DJANGO_ADMIN_* variables
python manage.py seed_initial --if-empty

exec "$@"
