FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and transcript corpus
COPY src/ ./src/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Ingest transcript knowledge base on build
RUN python scripts/ingest.py

EXPOSE 8000

# Run FastAPI backend with Uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
