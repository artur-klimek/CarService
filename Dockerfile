# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=development \
    FLASK_DEBUG=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p /app/logs

# Copy the entire project
COPY . .

# Set permissions
RUN chmod -R 755 /app

# Print project structure for verification
RUN echo "=== Project Structure ===" && \
    ls -la /app && \
    echo "=== App Directory ===" && \
    ls -la /app/app && \
    echo "=== Templates Directory ===" && \
    ls -la /app/app/templates && \
    echo "=== Auth Templates Directory ===" && \
    ls -la /app/app/templates/auth

# Create and configure config file
RUN python -c "from app.config import Config; Config()"

# Expose port
EXPOSE 5000

# Run the application
CMD ["flask", "run", "--host=0.0.0.0"] 