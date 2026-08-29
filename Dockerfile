# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CRM_ENV=production \
    CRM_PORT=8000

WORKDIR /app

# Copy dependency manifests
COPY requirements.txt pyproject.toml ./

# Install application dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Run database migrations and seeding on container bootstrap
RUN python seeds/mock_crm_data.py

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/').getcode()" || exit 1

CMD ["python", "main.py"]
