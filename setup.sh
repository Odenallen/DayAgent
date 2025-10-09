#!/bin/bash

echo "Setting up DayAgent..."

# Copy example configs if they don't exist
if [ ! -f app/google_keys.json ]; then
    echo "Please create app/google_keys.json from config.example/"
    exit 1
fi

if [ ! -f app/mcp_config.json ]; then
    cp config.example/mcp_config.json app/mcp_config.json
    echo "Created app/mcp_config.json - please edit with your settings"
fi

# Create directories
mkdir -p result pdfs

echo "Setup complete! Run: docker-compose up --build"