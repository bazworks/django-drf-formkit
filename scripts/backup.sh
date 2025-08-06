#!/bin/bash
# scripts/backup.sh

# Exit on error
set -e

# Configuration
timestamp=$(date +%Y%m%d_%H%M%S)
backup_dir="/opt/mspsquare/backups"
app_dir="/opt/mspsquare"

# Load MySQL credentials from .env file
if [ -f "$app_dir/.env" ]; then
    source "$app_dir/.env"
else
    echo "Error: .env file not found"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p $backup_dir

# Database backup
echo "Creating database backup..."
mysqldump -h localhost \
    -u "$MYSQL_USER" \
    -p"$MYSQL_PASSWORD" \
    "$MYSQL_NAME" > "$backup_dir/db_${timestamp}.sql"

# Media files backup
echo "Creating media files backup..."
tar -czf "$backup_dir/media_${timestamp}.tar.gz" \
    -C "$app_dir/backend/mspsquare" media/

# Static files backup
echo "Creating static files backup..."
tar -czf "$backup_dir/static_${timestamp}.tar.gz" \
    -C "$app_dir/backend/mspsquare" staticfiles/

# Keep only last 5 backups
echo "Cleaning up old backups..."
ls -t $backup_dir/db_* 2>/dev/null | tail -n +6 | xargs -r rm
ls -t $backup_dir/media_* 2>/dev/null | tail -n +6 | xargs -r rm
ls -t $backup_dir/static_* 2>/dev/null | tail -n +6 | xargs -r rm

echo "Backup completed successfully!"
echo "Backup files are stored in: $backup_dir"