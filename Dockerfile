FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt requirements-microsoft.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-microsoft.txt
COPY . .
RUN useradd --create-home --uid 10001 nexusmind && \
    mkdir -p /app/data && \
    chown -R nexusmind:nexusmind /app
USER nexusmind
EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
