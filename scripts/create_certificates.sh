#!/bin/bash

# Exit on error
set -e

# Check if domain argument is provided
if [ -z "$1" ]; then
    echo "Please provide a domain name as an argument"
    echo "Usage: ./create-certificates.sh example.com"
    exit 1
fi

DOMAIN=$1

# Stop nginx temporarily to free up port 80
sudo systemctl stop nginx

# Generate certificates using certbot
sudo certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email psathaye@gmail.com \
    --keep-until-expiring \
    -d $DOMAIN

# Start nginx again
sudo systemctl start nginx

echo "Certificates generated/renewed successfully!"
echo "Certificates are stored in /etc/letsencrypt/live/$DOMAIN/"

# Set up auto-renewal in crontab if not already set
if ! (crontab -l 2>/dev/null | grep -q "certbot renew"); then
    (crontab -l 2>/dev/null; echo "0 0 1 * * certbot renew --quiet && systemctl restart nginx") | crontab -
    echo "Added automatic renewal to crontab (monthly)"
fi