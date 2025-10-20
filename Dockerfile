FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock* ./

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry

# Отключаем создание виртуального окружения (не нужно в Docker)
RUN poetry config virtualenvs.create false

# Устанавливаем зависимости
RUN poetry install --no-dev --no-interaction --no-ansi

# Копируем весь проект
COPY . .

# Создаем директорию для базы данных
RUN mkdir -p /app/data

# Запускаем бота
CMD ["python", "main.py"]
