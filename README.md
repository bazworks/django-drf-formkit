# Django DRF Template

A comprehensive Django REST Framework template with built-in authentication, file management, email handling, and core functionality. This template is designed to be a starting point for building robust Django-based web applications.

## Features

### 1. Authentication System (`app_auth`)

- JWT-based authentication
- User registration and login
- Password reset functionality
- User profile management
- Role-based access control

### 2. File Management (`app_files`)

- File upload and download
- File storage with AWS S3 support
- File type validation
- Secure file access

### 3. Email System (`app_email`)

- Email templates
- AWS SES integration
- Email queue management
- Support for HTML and plain text emails

### 4. Core Functionality (`app_core`)

- Base models and utilities
- Common middleware
- Shared functionality
- System configurations

## Technical Stack

- **Backend**: Django 5.1.4 + Django REST Framework
- **Database**: MySQL (configurable)
- **Cache**: Redis
- **Task Queue**: Celery
- **File Storage**: AWS S3 (optional)
- **Email Service**: AWS SES (optional)
- **Server**: Nginx + Gunicorn
- **Process Management**: Supervisor

## Prerequisites

- Python 3.12 (Ubuntu 24.04 LTS)
- MySQL
- Redis
- Node.js (for frontend development)

## Setup Instructions

### 1. Environment Setup

1. Clone the repository
2. Copy `env.example` to `.env` and configure your environment variables:
   ```bash
   cp env.example .env
   ```
3. Update the following in `.env`:
   - Database credentials
   - AWS credentials (if using S3/SES)
   - Secret key
   - Allowed hosts
   - CORS settings

### 2. Database Setup

1. Run the MySQL setup script:
   ```bash
   ./server/scripts/setup_mysql.sh your-database-name
   ```
2. Run migrations:
   ```bash
   python manage.py migrate
   ```
3. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

### 3. Server Setup

1. Run the Ubuntu setup script:
   ```bash
   ./server/scripts/setup_ubuntu.sh your-project-name
   ```
2. Configure Nginx and Supervisor:
   - Nginx config: `server/config/nginx.conf`
   - Supervisor config: `server/config/supervisor.conf`

### 4. Development Setup

1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run development server:
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
├── app_auth/          # Authentication app
├── app_core/          # Core functionality
├── app_email/         # Email handling
├── app_files/         # File management
├── project/           # Project settings
├── server/            # Server configurations
│   ├── config/        # Nginx and Supervisor configs
│   └── scripts/       # Setup scripts
├── static/            # Static files
├── media/             # User-uploaded files
└── requirements.txt   # Python dependencies
```

## Additional Configuration

### AWS Services

If using AWS services (S3/SES):

1. Configure AWS credentials in `.env`
2. Set `USE_S3=True` for S3 storage
3. Set `USE_SES=True` for SES email

### Logging

- Configure log level in `.env`
- Set `USE_JSON_LOGS=true` for JSON format logs

### CORS

Configure allowed origins in `.env`:

```
CORS_ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
```

## Development Guidelines

1. Follow PEP 8 style guide
2. Use type hints
3. Write tests for new features
4. Update documentation for API changes

## Deployment

1. Set `DEBUG=False` in production
2. Configure proper `ALLOWED_HOSTS`
3. Use proper SSL certificates
4. Set up proper backup strategy
5. Configure monitoring and logging

## Security Considerations

1. Keep `SECRET_KEY` secure
2. Use environment variables for sensitive data
3. Configure proper CORS settings
4. Set up proper file permissions
5. Use HTTPS in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your License Here]
