#!/bin/bash
# Build and run the Grow Aloe CRM Docker container

set -e

echo "🚀 Building Grow Aloe CRM Docker container..."

# Build the Docker image
docker build -t grow-aloe-crm .

echo "✅ Build complete!"
echo ""
echo "🔄 Starting the container..."

# Stop and remove existing container if it exists
docker stop grow-aloe-crm-container 2>/dev/null || true
docker rm grow-aloe-crm-container 2>/dev/null || true

# Run the container with all required ports exposed
docker run -d \
  --name grow-aloe-crm-container \
  -p 80:80 \
  -p 3000:3000 \
  -p 8000:8000 \
  -p 5432:5432 \
  -p 6379:6379 \
  grow-aloe-crm

echo "✅ Container started successfully!"
echo ""
echo "📋 Access Information:"
echo "   🌐 Frontend (Production): http://localhost"
echo "   🛠️  Frontend (Dev Server): http://localhost:3000"
echo "   🔗 Django API: http://localhost:8000/api/"
echo "   👤 Django Admin: http://localhost:8000/admin/"
echo "   🗄️  PostgreSQL: localhost:5432"
echo "   📊 Redis: localhost:6379"
echo ""
echo "🔑 Default Admin Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   Email: admin@growaloe.com"
echo ""
echo "📊 To check container status:"
echo "   docker logs -f grow-aloe-crm-container"
echo ""
echo "🛑 To stop the container:"
echo "   docker stop grow-aloe-crm-container"
