# Используем официальный Python 3.11
FROM python:3.11-slim

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем pip-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY . .

# Указываем порт Render
ENV PORT=8000

# Команда запуска
CMD ["uvicorn", "bot:app", "--host", "0.0.0.0", "--port", "8000"]
