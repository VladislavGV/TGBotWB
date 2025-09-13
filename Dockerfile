# Python 3.11
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Запуск uvicorn на порту 8000
CMD ["uvicorn", "bot:app", "--host", "0.0.0.0", "--port", "8000"]
