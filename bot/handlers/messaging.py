import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.main_kb import get_user_list_keyboard, get_cancel_keyboard, get_confirm_keyboard
from bot.database.db import Database
from bot.utils.permissions import can_send_messages

router = Router()


class MessageStates(StatesGroup):
    selecting_recipients = State()
    entering_message = State()
    confirming = State()


def get_reply_keyboard(sender_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой 'Ответить'"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Ответить",
                    callback_data=f"reply_{sender_id}"
                )
            ]
        ]
    )
    return keyboard


@router.message(F.text == "📤 Отправить сообщение")
async def start_messaging(message: Message, state: FSMContext, db: Database):
    """Начать процесс отправки сообщения"""
    # Проверяем права на отправку
    if not await can_send_messages(message.from_user.id, db):
        await message.answer(
            "❌ У вас нет прав для отправки сообщений.\n\n"
            "Обратитесь к администратору бота."
        )
        return

    users = await db.get_all_users(exclude_user_id=message.from_user.id)

    if not users:
        await message.answer(
            "❌ В боте пока нет других пользователей.\n\n"
            "Пригласите друзей написать боту /start!"
        )
        return

    # Инициализируем данные
    await state.update_data(selected_users=[])

    await message.answer(
        "📤 <b>Отправка сообщения</b>\n\n"
        "1️⃣ Выберите получателей из списка.\n"
        "Нажмите на пользователя для выбора/отмены.\n\n"
        "После выбора нажмите '✅ Готово'",
        reply_markup=get_user_list_keyboard(users),
        parse_mode="HTML"
    )
    await state.set_state(MessageStates.selecting_recipients)


@router.callback_query(MessageStates.selecting_recipients, F.data.startswith("toggle_user_"))
async def toggle_user(callback: CallbackQuery, state: FSMContext, db: Database):
    """Переключить выбор пользователя"""
    user_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    selected = data.get('selected_users', [])

    if user_id in selected:
        selected.remove(user_id)
        action = "убран из"
    else:
        selected.append(user_id)
        action = "добавлен в"

    await state.update_data(selected_users=selected)

    # Обновляем клавиатуру
    users = await db.get_all_users(exclude_user_id=callback.from_user.id)
    buttons = []

    for user in users:
        display_name = user.get('username') and f"@{user['username']}" or \
                      f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or \
                      f"ID: {user['user_id']}"

        checkbox = "☑" if user['user_id'] in selected else "☐"
        buttons.append([
            InlineKeyboardButton(
                text=f"{checkbox} {display_name}",
                callback_data=f"toggle_user_{user['user_id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text=f"✅ Готово ({len(selected)} выбрано)", callback_data="done_selecting_users")
    ])
    buttons.append([
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(f"Пользователь {action} список")


@router.callback_query(MessageStates.selecting_recipients, F.data == "done_selecting_users")
async def done_selecting_users(callback: CallbackQuery, state: FSMContext):
    """Завершить выбор получателей"""
    data = await state.get_data()
    selected = data.get('selected_users', [])

    if not selected:
        await callback.answer("❌ Выберите хотя бы одного пользователя!", show_alert=True)
        return

    await callback.message.edit_text(
        f"✅ Выбрано: {len(selected)} получателей\n\n"
        "2️⃣ Теперь отправьте мне текст сообщения.\n\n"
        "💡 Поддерживается:\n"
        "• Форматирование текста\n"
        "• Ссылки\n"
        "• Эмодзи",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(MessageStates.entering_message)
    await callback.answer()


@router.message(MessageStates.entering_message, F.text)
async def enter_message_text(message: Message, state: FSMContext, db: Database):
    """Получить текст сообщения"""
    message_text = message.text

    # Сохраняем текст
    await state.update_data(message_text=message_text)

    data = await state.get_data()
    selected_count = len(data.get('selected_users', []))

    # Получаем имя отправителя для предпросмотра
    sender_name = message.from_user.username and f"@{message.from_user.username}" or message.from_user.first_name

    preview = f"""
━━━━━━━━━━━━━━━━
📨 <b>Сообщение от {sender_name}</b>

{message_text}

━━━━━━━━━━━━━━━━
<i>Отправлено через бота</i>
    """

    await message.answer(
        "📝 <b>Предпросмотр сообщения:</b>\n\n" + preview +
        f"\n\n📊 Будет отправлено <b>{selected_count}</b> получателям.\n\n"
        "❓ Отправить?",
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(MessageStates.confirming)


@router.callback_query(MessageStates.confirming, F.data == "confirm_yes")
async def confirm_send(callback: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    """Подтвердить и отправить сообщения"""
    data = await state.get_data()
    selected_users = data.get('selected_users', [])
    message_text = data.get('message_text')

    await callback.message.edit_text(
        "⏳ Отправляю сообщения...\n"
        "Пожалуйста, подождите.",
        parse_mode="HTML"
    )

    # Получаем информацию об отправителе
    sender = await db.get_user_by_id(callback.from_user.id)
    sender_name = sender.get('username') and f"@{sender['username']}" or sender.get('first_name')

    # Форматируем сообщение
    formatted_message = f"""━━━━━━━━━━━━━━━━
📨 <b>Сообщение от {sender_name}</b>

{message_text}

━━━━━━━━━━━━━━━━
"""

    # Создаем запись о рассылке
    broadcast_id = await db.add_broadcast(
        sender_id=callback.from_user.id,
        message_text=message_text,
        total_recipients=len(selected_users)
    )

    # Отправляем сообщения
    successful = 0
    failed = 0
    failed_users = []

    for user_id in selected_users:
        try:
            # Отправляем с кнопкой "Ответить"
            await bot.send_message(
                chat_id=user_id,
                text=formatted_message,
                reply_markup=get_reply_keyboard(callback.from_user.id),
                parse_mode="HTML"
            )
            # Сохраняем в историю
            await db.add_message(callback.from_user.id, user_id, message_text)
            successful += 1
            # Задержка между сообщениями
            await asyncio.sleep(0.5)
        except Exception as e:
            failed += 1
            user = await db.get_user_by_id(user_id)
            if user:
                display_name = user.get('username') and f"@{user['username']}" or \
                              user.get('first_name') or f"ID: {user_id}"
                failed_users.append(display_name)

    # Обновляем статистику
    await db.update_broadcast_stats(broadcast_id, successful, failed)

    # Формируем отчет
    report = f"""✅ <b>Рассылка завершена!</b>

📊 <b>Статистика:</b>
✅ Успешно: {successful}
❌ Не удалось: {failed}
📈 Всего: {len(selected_users)}
"""

    if failed_users:
        report += f"\n\n❌ <b>Не удалось отправить:</b>\n"
        for user in failed_users[:5]:
            report += f"• {user}\n"
        if len(failed_users) > 5:
            report += f"... и еще {len(failed_users) - 5}"

    await callback.message.edit_text(report, parse_mode="HTML")
    await state.clear()
    await callback.answer()


@router.callback_query(MessageStates.confirming, F.data == "confirm_no")
async def cancel_send(callback: CallbackQuery, state: FSMContext):
    """Отменить отправку"""
    await callback.message.edit_text("❌ Отправка отменена.")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("reply_"))
async def start_reply(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начать ответ на сообщение"""
    # Проверяем права на отправку
    if not await can_send_messages(callback.from_user.id, db):
        await callback.answer(
            "❌ У вас нет прав для отправки сообщений.",
            show_alert=True
        )
        return

    sender_id = int(callback.data.split("_")[1])

    # Получаем информацию об отправителе
    sender = await db.get_user_by_id(sender_id)
    if not sender:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    sender_name = sender.get('username') and f"@{sender['username']}" or sender.get('first_name')

    # Сохраняем ID получателя
    await state.update_data(
        selected_users=[sender_id],
        reply_to=sender_name
    )

    await callback.message.answer(
        f"💬 <b>Ответ для {sender_name}</b>\n\n"
        "Отправьте мне текст ответа:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(MessageStates.entering_message)
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отменить действие"""
    await callback.message.edit_text("❌ Действие отменено.")
    await state.clear()
    await callback.answer()
