# Используем официальный Python 3.11 образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Указываем порт, который будет слушать Render
EXPOSE 8000

# Команда запуска бота
CMD ["python", "bot.py"]
