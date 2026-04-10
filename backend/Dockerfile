FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    ffmpeg \
    postgresql-client \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy application code being handled by volume mount in dev, 
# but good to have for prod builds
COPY . .

# Environment variables
ENV PYTHONPATH=/app

# Download Kokoro ONNX weights and voices before starting the server
RUN python app/models/kokoro_setup.py

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload", "--reload-exclude", "*.pyc", "--reload-exclude", "*__pycache__*", "--reload-exclude", "uploads/*", "--reload-exclude", "data/*", "--reload-exclude", "*.log", "--reload-exclude", ".git/*", "--reload-exclude", ".pytest_cache/*", "--reload-exclude", ".vscode/*", "--reload-exclude", "*.sqlite", "--reload-exclude", "*.tmp", "--reload-exclude", "venv/*", "--reload-exclude", "node_modules/*", "--reload-exclude", ".idea/*"]
