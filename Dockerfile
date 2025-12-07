FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api_simple.py /app/api_simple.py

ENV PYTHONUNBUFFERED=1

CMD ["python", "api_simple.py"]
