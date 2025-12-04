FROM python:3.11-slim

WORKDIR /app

COPY api_simple.py /app/api_simple.py

RUN pip install --no-cache-dir fastapi uvicorn prometheus-client

ENV PYTHONUNBUFFERED=1

CMD ["python", "api_simple.py"]
