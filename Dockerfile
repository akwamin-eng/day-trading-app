# Dockerfile
# CACHE_BUSTER=2025-08-18-1000   <-- Add this

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    python -c "from telegram import Bot; print('✅ Confirmed: telegram module is installed')"

# Copy application
COPY . .

# Expose port
ENV PORT=8080
EXPOSE 8080

# Run the app
CMD ["python", "main.py"]
