#!/bin/bash

# Check if project name is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <project_name>"
    exit 1
fi

PROJECT_NAME=$1
PROJECT_USER="ubuntu"
PROJECT_PATH="/opt/${PROJECT_NAME}"
CONFIG_PATH="${PROJECT_PATH}/server/config"

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y


# Install system dependencies
sudo apt-get install -y \
    build-essential \
    libpq-dev \
    nginx \
    supervisor \
    redis-server \
    mysql-server \
    mysql-client \
    libmysqlclient-dev \
    git \
    curl

# Install Node.js and npm (if needed for frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Create project directory
sudo mkdir -p ${PROJECT_PATH}
sudo chown -R ${PROJECT_USER}:${PROJECT_USER} ${PROJECT_PATH}



# Setup Nginx
sudo cp ${CONFIG_PATH}/nginx.conf /etc/nginx/sites-available/${PROJECT_NAME}
sudo ln -s /etc/nginx/sites-available/${PROJECT_NAME} /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Setup Supervisor
sudo cp ${CONFIG_PATH}/supervisor.conf /etc/supervisor/conf.d/${PROJECT_NAME}.conf

# Create necessary directories
sudo mkdir -p /var/log/${PROJECT_NAME}
mkdir -p ${PROJECT_PATH}/media
mkdir -p ${PROJECT_PATH}/static

# Set permissions

sudo chown -R ${PROJECT_USER}:${PROJECT_USER} /var/log/${PROJECT_NAME}

# Restart services
sudo systemctl restart nginx
sudo systemctl restart supervisor
sudo systemctl restart redis-server
sudo systemctl restart mysql

echo "Setup completed successfully for project: ${PROJECT_NAME}"
echo "Project location: ${PROJECT_PATH}"