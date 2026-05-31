#!/bin/bash

# Cleanup old containers script
echo "=== Container Cleanup Script ==="
echo "This will remove old/stopped containers to free up space"
echo ""

# Show current containers
echo "Current containers:"
docker ps -a

echo ""
read -p "Remove all stopped containers? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing stopped containers..."
    docker container prune -f
    
    echo "Removing unused images..."
    docker image prune -f
    
    echo "Removing unused networks..."
    docker network prune -f
    
    echo ""
    echo "✅ Cleanup completed!"
    echo ""
    echo "Current containers after cleanup:"
    docker ps -a
else
    echo "Cancelled."
fi