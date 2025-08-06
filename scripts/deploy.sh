#!/bin/bash
set -e

# Pull latest changes
cd /opt/django-drf
git pull --rebase

# Deploy Backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# Restart services using supervisor
sudo services supervisor restart

# reload nginx
sudo systemctl reload nginx

echo "Deployment complete!"
