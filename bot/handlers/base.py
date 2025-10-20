from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.keyboards.main_kb import get_main_keyboard
from bot.database.db import Database

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

    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот-посредник для отправки сообщений.\n\n"
        "📤 Любой пользователь бота может отправить сообщение другим пользователям через меня.\n\n"
        "🔐 Все пользователи видят друг друга в общем списке.\n\n"
        "Выбери действие из меню ниже:",
        reply_markup=get_main_keyboard()
    )


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
<b>📖 Инструкция по использованию бота</b>

<b>🤖 Как это работает:</b>
Этот бот — посредник для отправки сообщений между пользователями.
Любой может отправить сообщение любому через бота.

<b>1️⃣ Отправка сообщения:</b>
• Нажмите "📤 Отправить сообщение"
• Выберите получателей из списка пользователей бота
• Введите текст сообщения
• Подтвердите отправку!

<b>2️⃣ Ответ на сообщение:</b>
• Когда вам придет сообщение, нажмите "💬 Ответить"
• Введите текст ответа
• Сообщение будет отправлено отправителю

<b>3️⃣ Просмотр пользователей:</b>
• Нажмите "👥 Список пользователей"
• Вы увидите всех, кто когда-либо писал боту

<b>⚠️ Важно:</b>
• Пользователь должен написать боту /start, чтобы получать сообщения
• Сообщения приходят ОТ БОТА, но с указанием отправителя
• Не злоупотребляйте рассылками - это спам

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
