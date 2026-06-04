#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting FastAPI backend on 127.0.0.1:8000..."
# Start FastAPI backend in the background. We force HOST=127.0.0.1 and PORT=8000
# so it does not conflict with the external PORT exposed by Hugging Face Spaces.
cd backend
HOST=127.0.0.1 PORT=8000 python main.py &
cd ..

echo "Starting Next.js frontend on port ${PORT:-7860}..."
# Start Next.js frontend. The PORT environment variable is automatically
# passed by Hugging Face Spaces (defaulting to 7860) and respected by next start.
exec npm run start
