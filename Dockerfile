# Используем легкий официальный образ Python (подойдет для Render)
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Установим системные зависимости, необходимые для сборки пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы
COPY requirements.txt /app/requirements.txt
COPY bot.py /app/bot.py

# Установим зависимости
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Переменные окружения для безопасности
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Порт для health-check (Render читает PORT env var)
EXPOSE 8080

# Команда запуска
CMD ["python", "/app/bot.py"]
