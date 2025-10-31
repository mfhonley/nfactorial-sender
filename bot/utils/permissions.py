from bot.database.db import Database

SUPER_ADMIN_ID = 803817300


def is_super_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь супер админом"""
    return user_id == SUPER_ADMIN_ID


async def is_admin(user_id: int, db: Database) -> bool:
    """Проверить, является ли пользователь обычным админом"""
    return await db.is_admin(user_id)


async def can_send_messages(user_id: int, db: Database) -> bool:
    """Проверить, может ли пользователь отправлять сообщения (админ или супер админ)"""
    if is_super_admin(user_id):
        return True
    return await is_admin(user_id, db)


async def get_user_role(user_id: int, db: Database) -> str:
    """Получить роль пользователя"""
    if is_super_admin(user_id):
        return "super_admin"
    elif await is_admin(user_id, db):
        return "admin"
    else:
        return "user"
