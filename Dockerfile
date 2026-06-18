FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN mkdir -p /app/logs /app/config

ENV CONFIG_DIR=/app/config \
    CONFIG_PATH=/app/config/config.json \
    LOG_DIR=/app/logs

EXPOSE 8080

CMD ["python", "app.py"]
