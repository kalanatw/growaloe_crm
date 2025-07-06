# Grow Aloe CRM - Docker Single Container Setup

This Docker configuration provides a complete single-container solution for the Grow Aloe CRM application, including all necessary services.

## 🏗️ What's Included

The single Docker container includes:
- **Django Backend** (Port 8000) - REST API and admin interface
- **React Frontend** - Both production build (served by Nginx on port 80) and dev server (port 3000)
- **PostgreSQL Database** (Port 5432) - Persistent data storage
- **Redis** (Port 6379) - Caching and session management
- **Nginx** (Port 80) - Web server for production frontend and API proxy
- **Supervisor** - Process management for all services

## 🚀 Quick Start

### Prerequisites
- Docker installed on your system
- At least 4GB of available RAM
- Ports 80, 3000, 8000, 5432, and 6379 available

### Build and Run
```bash
# Make scripts executable (if needed)
chmod +x docker-run.sh docker-cleanup.sh

# Build and start the container
./docker-run.sh
```

### Access the Application
- **Production Frontend**: http://localhost (Nginx-served React build)
- **Development Frontend**: http://localhost:3000 (React dev server with hot reload)
- **Django API**: http://localhost:8000/api/
- **Django Admin**: http://localhost:8000/admin/
- **Database**: postgresql://growaloe:growaloe123@localhost:5432/growaloe_db
- **Redis**: redis://localhost:6379

### Default Admin User
- **Username**: admin
- **Password**: admin123
- **Email**: admin@growaloe.com

## 📋 Container Services

### Service Management
All services are managed by Supervisor and start automatically:

1. **PostgreSQL** - Database service starts first
2. **Redis** - Cache service starts second
3. **Django** - Backend API service
4. **React Dev Server** - Frontend development server with hot reload
5. **Nginx** - Web server for production frontend and API proxy

### Service Logs
View logs for all services:
```bash
docker logs -f grow-aloe-crm-container
```

View specific service logs inside the container:
```bash
docker exec -it grow-aloe-crm-container tail -f /var/log/supervisor/django.log
docker exec -it grow-aloe-crm-container tail -f /var/log/supervisor/nginx.log
docker exec -it grow-aloe-crm-container tail -f /var/log/supervisor/postgresql.log
```

## 🛠️ Development Features

### Two Frontend Options
1. **Production Build** (Port 80): Optimized React build served by Nginx
2. **Development Server** (Port 3000): Live reload React dev server for development

### Database Auto-Setup
- Automatically creates PostgreSQL database and user
- Runs Django migrations on startup
- Creates default admin user
- Collects static files

### CORS Configuration
- CORS is properly configured for both port 80 and 3000
- API accessible from both frontend versions

## 🔧 Customization

### Environment Variables
The container creates a Django `.env` file with these settings:
```env
SECRET_KEY=django-insecure-docker-dev-key-change-in-production
DEBUG=True
DATABASE_URL=postgresql://growaloe:growaloe123@localhost:5432/growaloe_db
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:80,http://localhost:8000
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

### Modifying Configuration
To customize the setup:
1. Edit the `Dockerfile` 
2. Rebuild the container: `./docker-cleanup.sh && ./docker-run.sh`

## 📊 Monitoring and Management

### Container Status
```bash
# Check if container is running
docker ps | grep grow-aloe-crm-container

# View container resource usage
docker stats grow-aloe-crm-container

# View all logs
docker logs grow-aloe-crm-container
```

### Access Container Shell
```bash
docker exec -it grow-aloe-crm-container bash
```

### Django Management Commands
```bash
# Access Django shell
docker exec -it grow-aloe-crm-container /opt/venv/bin/python /app/backend/manage.py shell

# Run migrations
docker exec -it grow-aloe-crm-container /opt/venv/bin/python /app/backend/manage.py migrate

# Create additional superuser
docker exec -it grow-aloe-crm-container /opt/venv/bin/python /app/backend/manage.py createsuperuser
```

## 🧹 Cleanup

### Stop and Remove Container
```bash
./docker-cleanup.sh
```

### Manual Cleanup
```bash
# Stop container
docker stop grow-aloe-crm-container

# Remove container
docker rm grow-aloe-crm-container

# Remove image
docker rmi grow-aloe-crm
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**
   - Stop services using required ports (80, 3000, 8000, 5432, 6379)
   - Or modify port mappings in `docker-run.sh`

2. **Container Won't Start**
   - Check Docker logs: `docker logs grow-aloe-crm-container`
   - Ensure sufficient system resources (4GB+ RAM)

3. **Database Connection Issues**
   - Wait for PostgreSQL to fully start (check logs)
   - Database takes ~10-15 seconds to initialize on first run

4. **Frontend Not Loading**
   - Check if Nginx is running: `docker exec grow-aloe-crm-container service nginx status`
   - Verify React build was created: `docker exec grow-aloe-crm-container ls -la /app/frontend/build`

### Health Check
The container includes a health check that verifies the API is accessible:
```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' grow-aloe-crm-container
```

## 📝 Notes

- **Security**: This configuration is for development. Change passwords and secrets for production use.
- **Data Persistence**: Database data is stored inside the container and will be lost when the container is removed.
- **Performance**: All services in one container may impact performance compared to separate containers.
- **Scalability**: For production, consider using docker-compose with separate containers for each service.

## 🤝 Support

If you encounter issues:
1. Check the container logs
2. Verify all required ports are available
3. Ensure Docker has sufficient resources allocated
4. Check the troubleshooting section above
