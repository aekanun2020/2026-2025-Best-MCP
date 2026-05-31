#!/bin/bash

# ⚠️  WARNING: This script uses docker-compose down which REMOVES containers
# ⚠️  Use rebuild-safe.sh instead to preserve data
# ⚠️  This script is kept for reference only

echo "❌ ERROR: This script is disabled to prevent data loss"
echo ""
echo "Please use one of these safe alternatives:"
echo "  ./rebuild-safe.sh   - Rebuild only pyragdoc (preserves data)"
echo "  ./start-all.sh      - Start all containers"
echo "  ./check-status.sh   - Check container status"
echo ""
exit 1

# Original code (disabled):
# docker-compose down
# chmod +x ollama-entrypoint.sh
# docker-compose build --no-cache
# docker-compose up
