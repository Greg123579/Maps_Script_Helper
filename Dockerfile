# Dockerfile for FastAPI backend
FROM python:3.11-slim

# Install Docker CLI (needed to run docker commands from within container)
# Also install curl for health checks
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire project (will be overridden by volume mount, but needed for initial setup)
COPY . /app

# Expose port
EXPOSE 8000

# Run uvicorn without reload for now (outputs directory changes were causing issues)
# For development with code changes, restart the container manually
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]

