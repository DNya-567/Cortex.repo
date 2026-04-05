# Context Engine Backend
# This Dockerfile builds the FastAPI backend only.
# Qdrant and Ollama must be running separately and reachable at:
#   - QDRANT_URL (default: http://localhost:6333)
#   - OLLAMA_URL (default: http://localhost:11434)

FROM python:3.13-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/

# Copy configuration
COPY .env.example .env

# Set Python path
ENV PYTHONPATH=/app

# Expose API port
EXPOSE 8000

# Start the FastAPI server
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

