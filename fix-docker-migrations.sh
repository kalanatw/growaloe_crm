#!/bin/bash

# Fix Docker Migration Issues Script
# This script helps resolve migration conflicts in the Docker environment

echo "=== Fixing Docker Migration Issues ==="

# Stop any running containers
echo "Stopping existing containers..."
docker stop $(docker ps -q --filter ancestor=grow-aloe-crm) 2>/dev/null || true
docker rm $(docker ps -aq --filter ancestor=grow-aloe-crm) 2>/dev/null || true

# Remove any dangling volumes
echo "Removing Docker volumes..."
docker volume prune -f

# Rebuild the Docker image with a clean slate
echo "Rebuilding Docker image..."
docker build -t grow-aloe-crm .

echo "=== Docker image rebuilt successfully ==="
echo "You can now run: ./docker-run.sh"
