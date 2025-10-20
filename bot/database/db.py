import aiosqlite
from typing import List, Optional


class Database:
    def __init__(self, db_path: str = "data/bot.db"):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица всех пользователей бота (общедоступная)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # История сообщений
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    recipient_id INTEGER NOT NULL,
                    message_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users(user_id),
                    FOREIGN KEY (recipient_id) REFERENCES users(user_id)
                )
            """)

            # История рассылок
            await db.execute("""
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    message_text TEXT NOT NULL,
                    total_recipients INTEGER NOT NULL,
                    successful_sends INTEGER DEFAULT 0,
                    failed_sends INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users(user_id)
                )
            """)

            await db.commit()

    async def add_user(self, user_id: int, username: str = None,
                      first_name: str = None, last_name: str = None):
        """Добавить или обновить пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, last_activity)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    last_activity = CURRENT_TIMESTAMP
            """, (user_id, username, first_name, last_name))
            await db.commit()

    async def get_all_users(self, exclude_user_id: int = None) -> List[dict]:
        """Получить список всех активных пользователей бота"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if exclude_user_id:
                async with db.execute("""
                    SELECT * FROM users
                    WHERE is_active = 1 AND user_id != ?
                    ORDER BY last_activity DESC
                """, (exclude_user_id,)) as cursor:
                    rows = await cursor.fetchall()
            else:
                async with db.execute("""
                    SELECT * FROM users
                    WHERE is_active = 1
                    ORDER BY last_activity DESC
                """) as cursor:
                    rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Получить пользователя по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM users WHERE user_id = ?
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def add_message(self, sender_id: int, recipient_id: int, message_text: str):
        """Сохранить отправленное сообщение в историю"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO messages (sender_id, recipient_id, message_text)
                VALUES (?, ?, ?)
            """, (sender_id, recipient_id, message_text))
            await db.commit()
            return cursor.lastrowid

    async def get_user_stats(self) -> dict:
        """Получить общую статистику (для админа)"""
        async with aiosqlite.connect(self.db_path) as db:
            # Всего пользователей
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_active = 1") as cursor:
                total_users = (await cursor.fetchone())[0]

            # Всего сообщений
            async with db.execute("SELECT COUNT(*) FROM messages") as cursor:
                total_messages = (await cursor.fetchone())[0]

            # Всего рассылок
            async with db.execute("SELECT COUNT(*) FROM broadcasts") as cursor:
                total_broadcasts = (await cursor.fetchone())[0]

            return {
                'total_users': total_users,
                'total_messages': total_messages,
                'total_broadcasts': total_broadcasts
            }

    async def get_recent_messages(self, limit: int = 50) -> List[dict]:
        """Получить последние сообщения (для админа)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT
                    m.*,
                    u1.username as sender_username,
                    u1.first_name as sender_first_name,
                    u2.username as recipient_username,
                    u2.first_name as recipient_first_name
                FROM messages m
                LEFT JOIN users u1 ON m.sender_id = u1.user_id
                LEFT JOIN users u2 ON m.recipient_id = u2.user_id
                ORDER BY m.created_at DESC
                LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def add_broadcast(self, sender_id: int, message_text: str,
                          total_recipients: int):
        """Добавить запись о рассылке"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO broadcasts (sender_id, message_text, total_recipients)
                VALUES (?, ?, ?)
            """, (sender_id, message_text, total_recipients))
            await db.commit()
            return cursor.lastrowid

    async def update_broadcast_stats(self, broadcast_id: int,
                                    successful: int, failed: int):
        """Обновить статистику рассылки"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE broadcasts
                SET successful_sends = ?, failed_sends = ?
                WHERE id = ?
            """, (successful, failed, broadcast_id))
            await db.commit()

    async def deactivate_user(self, user_id: int):
        """Деактивировать пользователя (soft delete)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users
                SET is_active = 0
                WHERE user_id = ?
            """, (user_id,))
            await db.commit()

    async def delete_user(self, user_id: int):
        """Полностью удалить пользователя (hard delete)"""
        async with aiosqlite.connect(self.db_path) as db:
            # Удаляем сообщения
            await db.execute("DELETE FROM messages WHERE sender_id = ? OR recipient_id = ?", (user_id, user_id))
            # Удаляем рассылки
            await db.execute("DELETE FROM broadcasts WHERE sender_id = ?", (user_id,))
            # Удаляем пользователя
            await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            await db.commit()
