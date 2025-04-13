#!/bin/bash

# Create data directory if it doesn't exist
mkdir -p data

# Build and start the container
docker-compose -f docker-compose.kasm.yml up -d

# Print instructions
echo "
PyPTV with Kasm is now running!

Access the PyPTV GUI by opening your web browser and navigating to:
http://localhost:6901

No password is required.

Your local 'data' directory is mounted to /home/kasm-default-profile/work inside the container.
Any files you save there will be accessible on your host system.

To stop the container, run: docker-compose -f docker-compose.kasm.yml down
"

# Open browser (if available)
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:6901
elif command -v open &> /dev/null; then
    open http://localhost:6901
elif command -v start &> /dev/null; then
    start http://localhost:6901
fi
