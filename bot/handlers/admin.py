from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database.db import Database

router = Router()

ADMIN_ID = 803817300  # Твой ID


class AdminStates(StatesGroup):
    deleting_user = State()


def is_admin(user_id: int) -> bool:
    """Проверка на админа"""
    return user_id == ADMIN_ID


@router.message(Command("admin"))
async def admin_panel(message: Message, db: Database):
    """Админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return

    stats = await db.get_user_stats()

    text = f"""
🔐 <b>АДМИН-ПАНЕЛЬ</b>

📊 <b>Общая статистика:</b>
👥 Всего пользователей: {stats['total_users']}
💬 Всего сообщений: {stats['total_messages']}
📤 Всего рассылок: {stats['total_broadcasts']}
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users")
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
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    stats = await db.get_user_stats()

    # Добавляем timestamp чтобы текст всегда был разный
    import datetime
    now = datetime.datetime.now().strftime("%H:%M:%S")

    text = f"""
🔐 <b>АДМИН-ПАНЕЛЬ</b>

📊 <b>Общая статистика:</b>
👥 Всего пользователей: {stats['total_users']}
💬 Всего сообщений: {stats['total_messages']}
📤 Всего рассылок: {stats['total_broadcasts']}

<i>Обновлено: {now}</i>
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users")
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
    if not is_admin(callback.from_user.id):
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
    if not is_admin(callback.from_user.id):
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
    """Рассылка всем пользователям (только для админа)"""
    if not is_admin(message.from_user.id):
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
    """Удалить пользователя (только для админа)"""
    if not is_admin(message.from_user.id):
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
    if user_id == ADMIN_ID:
        await message.answer("❌ Нельзя удалить админа!")
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
    if not is_admin(callback.from_user.id):
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
    if not is_admin(callback.from_user.id):
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
