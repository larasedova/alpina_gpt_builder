# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=bot_builder.settings

# Создаем и переходим в рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями
COPY requirements.txt .
# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем пользователя для безопасности
RUN useradd -m -r django && chown -R django /app
USER django

# Открываем порт
EXPOSE 8000

# Запускаем приложение с gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "bot_builder.wsgi:application"]
