# Используем официальный Python
FROM python:3.11-slim

# Устанавливаем зависимости
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Порт Render
ENV PORT=10000

# Команда запуска
CMD ["python", "bot.py"]
