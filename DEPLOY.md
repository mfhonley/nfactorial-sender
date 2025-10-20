# Деплой бота

## Вариант 1: Docker Compose (Рекомендуется)

### Требования:
- Docker
- Docker Compose

### Запуск:

```bash
# 1. Убедись что .env файл настроен
cat .env

# 2. Запусти бота
docker-compose up -d

# 3. Проверь логи
docker-compose logs -f

# 4. Остановить бота
docker-compose down

# 5. Перезапустить бота
docker-compose restart
```

### Обновление кода:

```bash
# Остановить
docker-compose down

# Пересобрать образ
docker-compose build

# Запустить заново
docker-compose up -d
```

---

## Вариант 2: Docker (без compose)

```bash
# 1. Собрать образ
docker build -t telegram-sender-bot .

# 2. Запустить контейнер
docker run -d \
  --name sender-bot \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  telegram-sender-bot

# 3. Проверить логи
docker logs -f sender-bot

# 4. Остановить
docker stop sender-bot
docker rm sender-bot
```

---

## Вариант 3: Локально (Poetry)

```bash
# 1. Установить зависимости
poetry install

# 2. Запустить
poetry run python main.py

# Или через виртуальное окружение
poetry shell
python main.py
```

---

## Вариант 4: Локально (в фоне)

```bash
# Запустить в фоне
nohup poetry run python main.py > bot.log 2>&1 &

# Посмотреть логи
tail -f bot.log

# Найти процесс
ps aux | grep python

# Остановить
kill <PID>
```

---

## Вариант 5: На VPS (systemd)

### Создай файл `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Sender Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/sender
Environment="PATH=/path/to/sender/.venv/bin"
ExecStart=/path/to/sender/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Запуск через systemd:

```bash
# Перезагрузить systemd
sudo systemctl daemon-reload

# Запустить бота
sudo systemctl start telegram-bot

# Включить автозапуск
sudo systemctl enable telegram-bot

# Проверить статус
sudo systemctl status telegram-bot

# Посмотреть логи
sudo journalctl -u telegram-bot -f

# Перезапустить
sudo systemctl restart telegram-bot

# Остановить
sudo systemctl stop telegram-bot
```

---

## База данных

База данных хранится в папке `data/bot.db`

**Важно:** При использовании Docker, папка `data/` монтируется как volume, поэтому данные сохраняются даже при перезапуске контейнера.

### Бэкап базы:

```bash
# Создать бэкап
cp data/bot.db data/bot.db.backup

# Или с датой
cp data/bot.db data/bot.db.$(date +%Y%m%d_%H%M%S)
```

### Восстановление:

```bash
# Остановить бота
docker-compose down

# Восстановить из бэкапа
cp data/bot.db.backup data/bot.db

# Запустить бота
docker-compose up -d
```

---

## Мониторинг

### Проверка что бот работает:

```bash
# Docker Compose
docker-compose ps

# Docker
docker ps | grep sender-bot

# Локально
ps aux | grep python | grep main.py
```

### Логи:

```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f sender-bot

# Локально
tail -f bot.log

# Systemd
sudo journalctl -u telegram-bot -f
```

---

## Переменные окружения

Файл `.env` должен содержать:

```
BOT_TOKEN=your_bot_token_here
```

Опционально можно добавить:

```
ADMIN_ID=803817300
LOG_LEVEL=INFO
```

---

## Troubleshooting

### Бот не запускается:

```bash
# Проверить логи
docker-compose logs

# Проверить .env
cat .env

# Проверить что порты не заняты
netstat -tuln | grep 8080
```

### База данных повреждена:

```bash
# Остановить бота
docker-compose down

# Удалить старую базу
rm data/bot.db

# Запустить заново (создастся новая база)
docker-compose up -d
```

### Обновление кода:

```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Рекомендации для продакшена:

1. **Используй VPS** (DigitalOcean, Hetzner, AWS)
2. **Настрой автозапуск** (systemd или Docker restart policy)
3. **Делай бэкапы** базы данных ежедневно
4. **Мониторь логи** на ошибки
5. **Используй .env** для секретов (не коммить в Git)
6. **Настрой reverse proxy** (nginx) если нужен webhook

---

## Полезные команды:

```bash
# Посмотреть размер базы
du -h data/bot.db

# Почистить старые Docker образы
docker system prune -a

# Посмотреть использование ресурсов
docker stats

# Экспортировать логи
docker-compose logs > logs.txt
```

---

## Обновление зависимостей:

```bash
# Обновить Poetry
poetry update

# Пересобрать Docker образ
docker-compose build --no-cache
docker-compose up -d
```
