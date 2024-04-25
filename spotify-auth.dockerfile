# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's source code from your host to your image filesystem.
COPY . .

# Create a user to run your application (non-root user for security purposes)
RUN useradd -m myuser
USER myuser

# Expose port 8080 to the outside world
EXPOSE 8080

# Run the application
CMD ["python", "server.py"]
