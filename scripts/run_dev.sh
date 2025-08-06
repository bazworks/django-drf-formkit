#!/bin/bash

# Run the Django development server
python manage.py runserver 0.0.0.0:8000 &
celery -A project worker -l info &

# Wait for all processes to finish
wait


