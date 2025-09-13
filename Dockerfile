# Используем лёгкий официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости для сборки и работы (aiohttp, telegram и т.д.)
COPY requirements.txt .

RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порт для Render (Render сам задаёт PORT)
EXPOSE 8080

# Команда запуска
CMD ["python", "bot.py"]
