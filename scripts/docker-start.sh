#!/bin/bash
echo "Starting Jan-Sunwai AI with Docker..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    echo "Please start Docker first."
    exit 1
fi

echo "Building and starting containers..."
docker-compose up -d --build

echo ""
echo "Waiting for services to be ready..."
sleep 5

echo ""
echo "========================================"
echo "Jan-Sunwai AI is now running!"
echo "========================================"
echo "Backend API: http://localhost:8000"
echo "MongoDB: mongodb://localhost:27017"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
echo ""
