# Grow Aloe CRM - Comprehensive Single Container Dockerfile
# Includes: Django Backend, React Frontend, PostgreSQL, Redis, Nginx, Supervisor
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=development
ENV REACT_APP_API_URL=http://localhost:8000/api

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    postgresql-client \
    redis-server \
    nginx \
    supervisor \
    curl \
    wget \
    git \
    build-essential \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Create app directory
WORKDIR /app

# Copy entire project
COPY . .

# Set up Python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create logs directory for Django logging
RUN mkdir -p /app/backend/logs

# Install Python dependencies
WORKDIR /app/backend
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Install Node.js dependencies and build React frontend
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# Set up PostgreSQL
USER postgres
RUN /etc/init.d/postgresql start \
    && psql --command "CREATE USER growaloe WITH CREATEDB PASSWORD 'growaloe123';" \
    && createdb -O growaloe growaloe_db
USER root

# Create Django environment file
WORKDIR /app/backend
COPY <<EOF .env
SECRET_KEY=django-insecure-docker-dev-key-change-in-production
DEBUG=True
DATABASE_URL=postgresql://growaloe:growaloe123@localhost:5432/growaloe_db
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:80,http://localhost:8000
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
EOF

# Create superuser creation script
COPY <<EOF create_superuser.py
#!/usr/bin/env python3
import os
import django
from django.conf import settings
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_management.settings')
django.setup()

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@growaloe.com',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print("Superuser admin created successfully!")
else:
    print("Superuser admin already exists.")
EOF

# Configure Nginx
COPY <<EOF /etc/nginx/sites-available/default
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name _;
    
    # Serve React build files
    location / {
        root /app/frontend/build;
        try_files $uri $uri/ /index.html;
    }
    
    # Proxy Django API requests
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Proxy Django admin
    location /admin/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Serve Django static files
    location /static/ {
        alias /app/backend/staticfiles/;
    }
    
    # Serve Django media files
    location /media/ {
        alias /app/backend/media/;
    }
}
EOF

# Configure Supervisor
COPY <<EOF /etc/supervisor/conf.d/supervisord.conf
[supervisord]
nodaemon=true
user=root
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid

[program:postgresql]
command=/usr/lib/postgresql/14/bin/postgres -D /var/lib/postgresql/14/main -c config_file=/etc/postgresql/14/main/postgresql.conf
user=postgres
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/postgresql.log

[program:redis]
command=redis-server --port 6379 --bind 0.0.0.0
user=redis
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/redis.log

[program:django]
command=/opt/venv/bin/python manage.py runserver 0.0.0.0:8000
directory=/app/backend
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/django.log
environment=PATH="/opt/venv/bin"

[program:react-dev]
command=npm start
directory=/app/frontend
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/react-dev.log
environment=HOST="0.0.0.0",PORT="3000"

[program:nginx]
command=/usr/sbin/nginx -g "daemon off;"
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/nginx.log
EOF

# Create startup script
WORKDIR /app
COPY <<EOF startup.sh
#!/bin/bash
set -e

echo "Starting Grow Aloe CRM Services..."

# Start PostgreSQL
service postgresql start
sleep 5

# Start Redis
service redis-server start
sleep 2

# Set up Django
cd /app/backend
export PATH="/opt/venv/bin:$PATH"

echo "Running Django migrations..."
python manage.py migrate

echo "Creating superuser..."
python create_superuser.py

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting all services with Supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
EOF

RUN chmod +x /app/startup.sh

# Create log directories and redis user (if not exists)
RUN mkdir -p /var/log/supervisor \
    && (id -u redis >/dev/null 2>&1 || useradd --system --home /var/lib/redis --shell /bin/false redis)

# Expose all required ports
EXPOSE 80 3000 8000 5432 6379

# Set working directory
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost/api/ || exit 1

# Start all services
CMD ["/app/startup.sh"]
