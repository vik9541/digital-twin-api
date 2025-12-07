FROM python:3.11-slim
WORKDIR /app
COPY api_simple.py /app/api_simple.py
RUN pip install --no-cache-dir fastapi==0.104.1 uvicorn==0.24.0 prometheus-client==0.19.0
ENV PYTHONUNBUFFERED=1
CMD ["python", "api_simple.py"]
