from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📤 Отправить сообщение")
            ],
            [
                KeyboardButton(text="👥 Список пользователей"),
                KeyboardButton(text="📊 Статистика")
            ],
            [
                KeyboardButton(text="ℹ️ Помощь")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_broadcast_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для создания рассылки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Выбрать контакты", callback_data="select_contacts")
            ],
            [
                InlineKeyboardButton(text="📝 Ввести сообщение", callback_data="enter_message")
            ],
            [
                InlineKeyboardButton(text="🚀 Отправить рассылку", callback_data="send_broadcast")
            ],
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
            ]
        ]
    )
    return keyboard


def get_contacts_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для управления контактами"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить контакт", callback_data="add_contact")
            ],
            [
                InlineKeyboardButton(text="📋 Список контактов", callback_data="list_contacts")
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить контакт", callback_data="delete_contact")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
            ]
        ]
    )
    return keyboard


def get_user_list_keyboard(users: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком пользователей для выбора"""
    buttons = []

    for user in users:
        display_name = user.get('username') and f"@{user['username']}" or \
                      f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or \
                      f"ID: {user['user_id']}"

        buttons.append([
            InlineKeyboardButton(
                text=f"☐ {display_name}",
                callback_data=f"toggle_user_{user['user_id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="✅ Готово", callback_data="done_selecting_users")
    ])
    buttons.append([
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
            ]
        ]
    )
    return keyboard


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data="confirm_yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="confirm_no")
            ]
        ]
    )
    return keyboard
