FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    aria2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies globally using uv pip
RUN uv pip install --system .

# Copy application code
COPY main.py ./
COPY aniloader ./aniloader

# Create downloads directory
RUN mkdir -p /downloads

# Set default download directory
WORKDIR /downloads

# Entrypoint - use system python directly
ENTRYPOINT ["python", "/app/main.py"]
CMD ["--help"]
