# Развёртывание бота на Render

1. Создать новый **Web Service** на Render
2. Выбрать **Docker**.
3. Указать ветку репозитория и путь к `Dockerfile`
4. Порт: 8000
5. Build Command: оставьте пустым
6. Start Command: оставьте пустым, Render будет использовать CMD из Dockerfile

## Webhook

После деплоя получить URL сервиса, например:
