FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    REQUIRE_API_KEY=true \
    HF_HOME=/app/model-cache

WORKDIR /app
COPY requirements.txt requirements-microsoft.txt ./
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.5.1 && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-microsoft.txt
COPY . .
RUN useradd --create-home --uid 10001 nexusmind && \
    mkdir -p /app/data && \
    chown -R nexusmind:nexusmind /app
USER nexusmind
EXPOSE 8000
CMD ["python", "ops/serve.py"]
