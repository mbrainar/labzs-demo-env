FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# PORT is passed in via environment variable in docker-compose
CMD ["python", "app.py"]