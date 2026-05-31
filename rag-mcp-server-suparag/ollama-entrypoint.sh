#!/bin/bash
# Ollama entrypoint script - Pull required models

# Start Ollama server in background
ollama serve &

# Wait for server to start
echo "Waiting for Ollama server to start..."
sleep 10

# Pull required models
echo "Pulling qwen2.5:14b model..."
ollama pull qwen2.5:14b

echo "Pulling nomic-embed-text model..."
ollama pull nomic-embed-text

echo "✅ Ollama models ready!"

# Keep container running
wait
