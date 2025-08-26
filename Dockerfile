# Dockerfile for Render.com deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Render.com requires listening on PORT environment variable
EXPOSE 10000

# Run the web server wrapper (includes keep-alive and Discord bot)
CMD ["python", "web_server.py"]
