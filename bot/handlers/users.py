from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.main_kb import get_user_list_keyboard
from bot.database.db import Database

router = Router()


@router.message(F.text == "👥 Список пользователей")
async def show_users_list(message: Message, db: Database):
    """Показать список всех пользователей бота"""
    # Получаем всех пользователей кроме текущего
    users = await db.get_all_users(exclude_user_id=message.from_user.id)

    if not users:
        await message.answer(
            "📭 В боте пока нет других пользователей.\n\n"
            "Пригласите друзей написать боту /start!"
        )
        return

    text = "👥 <b>Пользователи бота:</b>\n\n"
    for i, user in enumerate(users[:20], 1):  # Показываем первых 20
        display_name = user.get('username') and f"@{user['username']}" or \
                      f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or \
                      f"ID: {user['user_id']}"

        text += f"{i}. {display_name}\n"

    if len(users) > 20:
        text += f"\n<i>...и еще {len(users) - 20} пользователей</i>"

    text += f"\n\n<b>Всего:</b> {len(users)} пользователей"

    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "show_users")
async def callback_show_users(callback: CallbackQuery, db: Database):
    """Показать список пользователей через callback"""
    users = await db.get_all_users(exclude_user_id=callback.from_user.id)

    if not users:
        await callback.answer("В боте пока нет других пользователей", show_alert=True)
        return

    text = "👥 <b>Выберите получателей:</b>\n\n"
    text += f"Всего пользователей: {len(users)}"

    await callback.message.edit_text(
        text,
        reply_markup=get_user_list_keyboard(users),
        parse_mode="HTML"
    )
    await callback.answer()
