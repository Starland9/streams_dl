# Stage 1: Base image with Python and Chrome
FROM python:3.12-slim-bullseye AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including Google Chrome for Selenium
RUN apt-get update && \
    apt-get install -y \
    wget \
    gnupg \
    # Add Google Chrome repository
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    # Install Chrome
    && apt-get update \
    && apt-get install -y google-chrome-stable
    # Clean up
    # && apt-get purge -y --auto-remove wget gnupg \
    # && rm -rf /var/lib/apt/lists/*

# Stage 2: Application setup
FROM base AS app

# Set working directory
WORKDIR /app

# Install Python dependencies
# First, copy only the requirements file to leverage Docker layer caching
COPY requirements.api.txt .
RUN pip install --no-cache-dir -r requirements.api.txt

# Copy only the necessary application source code
COPY api.py .
COPY src/models/ ./src/models/

# Expose the port the app runs on
EXPOSE 8092

# Define the command to run the application
# Use this for production. For development, you might want to use reload.
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8092"]

