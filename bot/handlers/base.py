from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.keyboards.main_kb import get_main_keyboard
from bot.database.db import Database
from bot.utils.permissions import can_send_messages, get_user_role

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """Обработчик команды /start"""
    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    # Проверяем роль пользователя для отображения правильного меню
    user_can_send = await can_send_messages(message.from_user.id, db)
    user_role = await get_user_role(message.from_user.id, db)

    # Формируем приветственное сообщение в зависимости от роли
    if user_role == "super_admin":
        greeting = (
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "🔐 <b>Вы — Супер Админ</b>\n\n"
            "Вы можете:\n"
            "• Отправлять сообщения пользователям\n"
            "• Управлять админами (/admin)\n"
            "• Просматривать всю статистику\n\n"
            "Выбери действие из меню ниже:"
        )
    elif user_role == "admin":
        greeting = (
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "👑 <b>Вы — Админ</b>\n\n"
            "Вы можете:\n"
            "• Отправлять сообщения пользователям\n"
            "• Просматривать список пользователей\n\n"
            "Выбери действие из меню ниже:"
        )
    else:
        greeting = (
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "Я бот-посредник для отправки сообщений.\n\n"
            "📬 Вы можете получать сообщения от админов бота.\n"
            "👥 Вы можете просматривать список пользователей.\n\n"
            "Выбери действие из меню ниже:"
        )

    await message.answer(
        greeting,
        reply_markup=get_main_keyboard(is_admin=user_can_send),
        parse_mode="HTML"
    )


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message, db: Database):
    """Обработчик команды /help"""
    user_role = await get_user_role(message.from_user.id, db)

    if user_role == "super_admin":
        help_text = """
<b>📖 Инструкция для Супер Админа</b>

<b>🔐 Ваши возможности:</b>
• Отправка сообщений пользователям
• Управление админами
• Просмотр полной статистики
• Удаление пользователей

<b>📊 Команды:</b>
/admin - Админ-панель
/add_admin USER_ID - Добавить админа
/remove_admin USER_ID - Удалить админа
/delete_user USER_ID - Удалить пользователя
/broadcast_all - Рассылка всем
/start - Начать работу
/help - Показать помощь
/stats - Статистика
        """
    elif user_role == "admin":
        help_text = """
<b>📖 Инструкция для Админа</b>

<b>👑 Ваши возможности:</b>
• Отправка сообщений пользователям
• Просмотр списка пользователей

<b>1️⃣ Отправка сообщения:</b>
• Нажмите "📤 Отправить сообщение"
• Выберите получателей из списка
• Введите текст сообщения
• Подтвердите отправку!

<b>2️⃣ Ответ на сообщение:</b>
• Когда вам придет сообщение, нажмите "💬 Ответить"
• Введите текст ответа

<b>📊 Команды:</b>
/start - Начать работу
/help - Показать помощь
/stats - Статистика
        """
    else:
        help_text = """
<b>📖 Инструкция по использованию бота</b>

<b>🤖 Как это работает:</b>
Этот бот — посредник для получения сообщений от админов.

<b>📬 Получение сообщений:</b>
• Сообщения приходят от админов бота
• Вы можете ответить, нажав кнопку "💬 Ответить"
• Ответ будет отправлен отправителю

<b>👥 Просмотр пользователей:</b>
• Нажмите "👥 Список пользователей"
• Вы увидите всех пользователей бота

<b>⚠️ Важно:</b>
• Обычные пользователи могут только получать сообщения
• Чтобы отправлять сообщения, обратитесь к администратору

<b>📊 Команды:</b>
/start - Начать работу
/help - Показать помощь
/stats - Статистика
        """

    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def cmd_stats(message: Message, db: Database):
    """Показать статистику бота"""
    stats = await db.get_user_stats()

    stats_text = f"""
<b>📊 Статистика бота</b>

👥 Всего пользователей: {stats['total_users']}
💬 Всего сообщений: {stats['total_messages']}
📤 Всего рассылок: {stats['total_broadcasts']}
    """

    await message.answer(stats_text, parse_mode="HTML")
