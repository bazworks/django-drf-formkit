#!/bin/bash

# Check if database name is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <database_name>"
    exit 1
fi

DB_NAME=$1
DB_USER="app_${DB_NAME}"
DB_PASSWORD=$(openssl rand -base64 12)  # Generate random password

# Create database
sudo mysql -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME};"

# Create user and grant privileges
sudo mysql -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';"
sudo mysql -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Update .env file
ENV_FILE=".env"

# Check if .env file exists, if not create from example
if [ ! -f "$ENV_FILE" ]; then
    cp env.example "$ENV_FILE"
fi

# Update database settings in .env
sed -i "s/MYSQL_DATABASE=.*/MYSQL_DATABASE=\"${DB_NAME}\"/" "$ENV_FILE"
sed -i "s/MYSQL_USER=.*/MYSQL_USER=\"${DB_USER}\"/" "$ENV_FILE"
sed -i "s/MYSQL_PASSWORD=.*/MYSQL_PASSWORD=\"${DB_PASSWORD}\"/" "$ENV_FILE"

echo "MySQL setup completed successfully!"
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Password: ${DB_PASSWORD}"
echo "These credentials have been updated in your .env file"