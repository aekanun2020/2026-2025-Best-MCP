# Dockerfile for Streamlit UI
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-ui.txt* ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    if [ -f requirements-ui.txt ]; then pip install --no-cache-dir -r requirements-ui.txt; fi

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
