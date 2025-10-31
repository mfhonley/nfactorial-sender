from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database.db import Database
from bot.utils.permissions import is_super_admin

router = Router()

SUPER_ADMIN_ID = 803817300  # Твой ID


class AdminStates(StatesGroup):
    deleting_user = State()


@router.message(Command("admin"))
async def admin_panel(message: Message, db: Database):
    """Админ-панель (только для супер админа)"""
    if not is_super_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return

    stats = await db.get_user_stats()
    admins = await db.get_all_admins()

    text = f"""
🔐 <b>СУПЕР АДМИН-ПАНЕЛЬ</b>

📊 <b>Общая статистика:</b>
👥 Всего пользователей: {stats['total_users']}
💬 Всего сообщений: {stats['total_messages']}
📤 Всего рассылок: {stats['total_broadcasts']}
👑 Админов: {len(admins)}
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton(text="👑 Управление админами", callback_data="admin_manage_admins")
            ],
            [
                InlineKeyboardButton(text="💬 Последние сообщения", callback_data="admin_messages")
            ],
            [
                InlineKeyboardButton(text="📊 Обновить статистику", callback_data="admin_stats")
            ]
        ]
    )

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery, db: Database):
    """Обновить статистику"""
    if not is_super_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    stats = await db.get_user_stats()
    admins = await db.get_all_admins()

    # Добавляем timestamp чтобы текст всегда был разный
    import datetime
    now = datetime.datetime.now().strftime("%H:%M:%S")

    text = f"""
🔐 <b>СУПЕР АДМИН-ПАНЕЛЬ</b>

📊 <b>Общая статистика:</b>
👥 Всего пользователей: {stats['total_users']}
💬 Всего сообщений: {stats['total_messages']}
📤 Всего рассылок: {stats['total_broadcasts']}
👑 Админов: {len(admins)}

<i>Обновлено: {now}</i>
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton(text="👑 Управление админами", callback_data="admin_manage_admins")
            ],
            [
                InlineKeyboardButton(text="💬 Последние сообщения", callback_data="admin_messages")
            ],
            [
                InlineKeyboardButton(text="📊 Обновить статистику", callback_data="admin_stats")
            ]
        ]
    )

    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer("✅ Обновлено")
    except Exception:
        # Если сообщение не изменилось, просто отвечаем
        await callback.answer("✅ Данные актуальны")


@router.callback_query(F.data == "admin_users")
async def admin_users_list(callback: CallbackQuery, db: Database):
    """Показать список всех пользователей"""
    if not is_super_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    users = await db.get_all_users()

    text = "👥 <b>Все пользователи бота:</b>\n\n"

    for i, user in enumerate(users[:50], 1):  # Показываем первых 50
        display_name = user.get('username') and f"@{user['username']}" or \
                      f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or \
                      f"Без имени"

        text += f"{i}. {display_name} (ID: {user['user_id']})\n"
        text += f"   └ Последняя активность: {user.get('last_activity', 'неизвестно')}\n\n"

    if len(users) > 50:
        text += f"\n<i>...и еще {len(users) - 50} пользователей</i>"

    text += f"\n\n<b>Всего:</b> {len(users)}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_stats")
            ]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_messages")
async def admin_messages_list(callback: CallbackQuery, db: Database):
    """Показать последние сообщения"""
    if not is_super_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    messages = await db.get_recent_messages(limit=20)

    if not messages:
        text = "📭 Сообщений пока нет."
    else:
        text = "💬 <b>Последние 20 сообщений:</b>\n\n"

        for i, msg in enumerate(messages, 1):
            sender = msg.get('sender_username') and f"@{msg['sender_username']}" or \
                    msg.get('sender_first_name', 'Неизвестно')
            recipient = msg.get('recipient_username') and f"@{msg['recipient_username']}" or \
                       msg.get('recipient_first_name', 'Неизвестно')

            message_preview = msg.get('message_text', '')[:50]
            if len(msg.get('message_text', '')) > 50:
                message_preview += "..."

            text += f"{i}. {sender} → {recipient}\n"
            text += f"   📝 {message_preview}\n"
            text += f"   🕐 {msg.get('created_at', 'неизвестно')}\n\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_stats")
            ]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.message(Command("broadcast_all"))
async def admin_broadcast(message: Message, db: Database):
    """Рассылка всем пользователям (только для супер админа)"""
    if not is_super_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    # Получаем текст после команды
    text = message.text.replace("/broadcast_all", "").strip()

    if not text:
        await message.answer(
            "📢 <b>Рассылка всем пользователям</b>\n\n"
            "Используйте команду:\n"
            "<code>/broadcast_all текст сообщения</code>",
            parse_mode="HTML"
        )
        return

    users = await db.get_all_users()

    await message.answer(f"⏳ Отправляю рассылку {len(users)} пользователям...")

    # TODO: Реализовать рассылку
    await message.answer(
        f"✅ Функция в разработке.\n"
        f"Планируется отправить сообщение {len(users)} пользователям."
    )


@router.message(Command("delete_user"))
async def delete_user_command(message: Message, db: Database):
    """Удалить пользователя (только для супер админа)"""
    if not is_super_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    # Получаем user_id после команды
    args = message.text.split()

    if len(args) < 2:
        await message.answer(
            "🗑 <b>Удаление пользователя</b>\n\n"
            "Используйте команду:\n"
            "<code>/delete_user USER_ID</code>\n\n"
            "Например: <code>/delete_user 123456789</code>\n\n"
            "Чтобы узнать ID пользователя, посмотрите в /admin → Список пользователей",
            parse_mode="HTML"
        )
        return

    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный формат ID. Используйте число.")
        return

    # Проверяем что пользователь существует
    user = await db.get_user_by_id(user_id)
    if not user:
        await message.answer(f"❌ Пользователь с ID {user_id} не найден.")
        return

    # Проверяем что не пытается удалить себя
    if user_id == SUPER_ADMIN_ID:
        await message.answer("❌ Нельзя удалить супер админа!")
        return

    display_name = user.get('username') and f"@{user['username']}" or \
                  user.get('first_name') or f"ID: {user_id}"

    # Создаем клавиатуру подтверждения
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚫 Деактивировать (soft)", callback_data=f"deactivate_{user_id}"),
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить навсегда (hard)", callback_data=f"delete_{user_id}"),
            ],
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_delete")
            ]
        ]
    )

    await message.answer(
        f"⚠️ <b>Удаление пользователя</b>\n\n"
        f"Пользователь: {display_name}\n"
        f"ID: {user_id}\n\n"
        f"<b>Выберите действие:</b>\n"
        f"• 🚫 Деактивировать - пользователь останется в базе, но не будет виден другим\n"
        f"• 🗑 Удалить навсегда - полное удаление из базы со всеми сообщениями",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("deactivate_"))
async def deactivate_user_callback(callback: CallbackQuery, db: Database):
    """Деактивировать пользователя"""
    if not is_super_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    user_id = int(callback.data.split("_")[1])

    await db.deactivate_user(user_id)

    await callback.message.edit_text(
        f"✅ Пользователь {user_id} деактивирован.\n\n"
        f"Он больше не виден в списке пользователей и не может получать сообщения.",
        parse_mode="HTML"
    )
    await callback.answer("✅ Деактивирован")


@router.callback_query(F.data.startswith("delete_"))
async def delete_user_callback(callback: CallbackQuery, db: Database):
    """Полностью удалить пользователя"""
    if not is_super_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    user_id = int(callback.data.split("_")[1])

    await db.delete_user(user_id)

    await callback.message.edit_text(
        f"✅ Пользователь {user_id} удален навсегда.\n\n"
        f"Все его сообщения и рассылки также удалены из базы.",
        parse_mode="HTML"
    )
    await callback.answer("✅ Удален")


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete_callback(callback: CallbackQuery):
    """Отменить удаление"""
    await callback.message.edit_text("❌ Удаление отменено.")
    await callback.answer()


# ============ УПРАВЛЕНИЕ АДМИНАМИ ============

@router.callback_query(F.data == "admin_manage_admins")
async def manage_admins(callback: CallbackQuery, db: Database):
    """Управление админами"""
    if not is_super_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    admins = await db.get_all_admins()

    if not admins:
        text = "👑 <b>Управление админами</b>\n\n❌ Нет админов."
    else:
        text = "👑 <b>Список админов:</b>\n\n"
        for i, admin in enumerate(admins, 1):
            display_name = admin.get('username') and f"@{admin['username']}" or \
                          admin.get('first_name') or f"ID: {admin['user_id']}"
            text += f"{i}. {display_name} (ID: {admin['user_id']})\n"
            text += f"   └ Добавлен: {admin.get('created_at', 'неизвестно')}\n\n"

    text += "\n\n<b>Команды:</b>\n"
    text += "• <code>/add_admin USER_ID</code> - добавить админа\n"
    text += "• <code>/remove_admin USER_ID</code> - удалить админа"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_stats")
            ]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.message(Command("add_admin"))
async def add_admin_command(message: Message, db: Database):
    """Добавить админа (только для супер админа)"""
    if not is_super_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    # Получаем user_id после команды
    args = message.text.split()

    if len(args) < 2:
        await message.answer(
            "👑 <b>Добавление админа</b>\n\n"
            "Используйте команду:\n"
            "<code>/add_admin USER_ID</code>\n\n"
            "Например: <code>/add_admin 123456789</code>\n\n"
            "Чтобы узнать ID пользователя, посмотрите в /admin → Список пользователей",
            parse_mode="HTML"
        )
        return

    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный формат ID. Используйте число.")
        return

    # Проверяем что пользователь существует
    user = await db.get_user_by_id(user_id)
    if not user:
        await message.answer(f"❌ Пользователь с ID {user_id} не найден в базе.")
        return

    # Проверяем что это не супер админ
    if user_id == SUPER_ADMIN_ID:
        await message.answer("❌ Супер админ не может быть добавлен как обычный админ!")
        return

    # Проверяем что пользователь еще не админ
    if await db.is_admin(user_id):
        await message.answer(f"❌ Пользователь {user_id} уже является админом.")
        return

    # Добавляем админа
    await db.add_admin(user_id, message.from_user.id)

    display_name = user.get('username') and f"@{user['username']}" or \
                  user.get('first_name') or f"ID: {user_id}"

    await message.answer(
        f"✅ <b>Пользователь добавлен в админы!</b>\n\n"
        f"Имя: {display_name}\n"
        f"ID: {user_id}\n\n"
        f"Теперь этот пользователь может отправлять сообщения другим пользователям бота.",
        parse_mode="HTML"
    )


@router.message(Command("remove_admin"))
async def remove_admin_command(message: Message, db: Database):
    """Удалить админа (только для супер админа)"""
    if not is_super_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    # Получаем user_id после команды
    args = message.text.split()

    if len(args) < 2:
        await message.answer(
            "👑 <b>Удаление админа</b>\n\n"
            "Используйте команду:\n"
            "<code>/remove_admin USER_ID</code>\n\n"
            "Например: <code>/remove_admin 123456789</code>",
            parse_mode="HTML"
        )
        return

    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный формат ID. Используйте число.")
        return

    # Проверяем что это не супер админ
    if user_id == SUPER_ADMIN_ID:
        await message.answer("❌ Нельзя удалить супер админа!")
        return

    # Проверяем что пользователь является админом
    if not await db.is_admin(user_id):
        await message.answer(f"❌ Пользователь {user_id} не является админом.")
        return

    # Удаляем админа
    await db.remove_admin(user_id)

    user = await db.get_user_by_id(user_id)
    display_name = user.get('username') and f"@{user['username']}" or \
                  user.get('first_name') or f"ID: {user_id}" if user else f"ID: {user_id}"

    await message.answer(
        f"✅ <b>Админ удален!</b>\n\n"
        f"Имя: {display_name}\n"
        f"ID: {user_id}\n\n"
        f"Теперь этот пользователь больше не может отправлять сообщения.",
        parse_mode="HTML"
    )
