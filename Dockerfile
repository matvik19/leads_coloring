FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /fastapi_app

# Устанавливаем необходимые утилиты, включая netcat-openbsd
RUN apt-get update && apt-get install -y netcat-openbsd

# Копируем файл зависимостей в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта в контейнер
COPY . .

EXPOSE 8000

# Указываем команду запуска
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "main:app"]
