FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry

# Отключаем создание виртуального окружения (не нужно в Docker)
RUN poetry config virtualenvs.create false

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock* ./

# Устанавливаем зависимости (без установки самого проекта)
RUN poetry install --only main --no-interaction --no-ansi --no-root

# Копируем весь проект
COPY . .

# Создаем директорию для базы данных
RUN mkdir -p /app/data

# Запускаем бота
CMD ["python", "main.py"]
