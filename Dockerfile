# ==============================================================================
# PyMorph AI - Dockerfile for Hugging Face Spaces & Container Deployments
# Created By: Prabu Arvind M
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system build tools and language runtimes (C, C++, Java JDK)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-jdk \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy python backend requirements and install dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application files (frontend, backend, root files)
COPY . /app

# Set permissions for user uploads and outputs
RUN mkdir -p /app/uploads /app/outputs && \
    chmod -R 777 /app/uploads /app/outputs

# Hugging Face Spaces default port is 7860 (can also be overridden by $PORT)
ENV PORT=7860
EXPOSE 7860

# Run FastAPI backend using Uvicorn
CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-7860}"]
