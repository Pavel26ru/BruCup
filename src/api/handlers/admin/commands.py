import asyncio
from aiogram import Router, types, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import ContentType, InlineKeyboardButton, InlineKeyboardMarkup
from src.api.filters import IsAdminFilter
from src.application.services.order_service import OrderService
from src.application.services.user_service import UserService
from src.application.states import Broadcast

admin_commands_router = Router()

@admin_commands_router.message(Command("orders"), IsAdminFilter())
async def get_active_orders(message: types.Message, order_service: OrderService):
    """
    Handles the /orders command for admins, displaying a list of active orders.
    """
    active_orders = await order_service.get_active_orders()

    if not active_orders:
        await message.answer("Активных заказов нет.")
        return

    response_text = "<b>Активные заказы:</b>\n\n"
    for order in active_orders:
        response_text += (
            f"<b>Заказ #{order.id}</b>\n"
            f"От: {order.user_id}\n"
            f"Адрес: {order.address}\n"
            f"Время: {order.pickup_time}\n"
            f"Статус: {order.status.value}\n"
            f"--- Состав ---\n"
            f"Напиток: {order.product_name} ({order.volume})\n"
            f"Кол-во: {order.quantity}\n"
        )
        if order.milk_name:
            response_text += f"Молоко: {order.milk_name}\n"
        if order.syrup_name:
            response_text += f"Сироп: {order.syrup_name}\n"
        response_text += f"<b>Итого: {order.total_price}₽</b>\n"
        response_text += "-------------------\n\n"

    # Telegram messages have a length limit of 4096 characters
    if len(response_text) > 4096:
        for i in range(0, len(response_text), 4096):
            await message.answer(response_text[i:i + 4096])
    else:
        await message.answer(response_text)

@admin_commands_router.message(Command("done"), IsAdminFilter())
async def complete_order_command(message: types.Message, command: CommandObject, order_service: OrderService, bot: Bot):
    """
    Handles the /done [order_id] command for admins.
    """
    if command.args is None:
        await message.answer("Пожалуйста, укажите ID заказа. Пример: `/done 123`")
        return

    try:
        order_id = int(command.args)
    except ValueError:
        await message.answer("ID заказа должен быть числом. Пример: `/done 123`")
        return

    order = await order_service.get_order_by_id(order_id)
    if not order:
        await message.answer(f"Заказ с ID {order_id} не найден или уже выполнен.")
        return
        
    if order.is_completed:
        await message.answer(f"Заказ #{order_id} уже был выполнен ранее.")
        return

    completed_order = await order_service.complete_order(order_id)
    if not completed_order:
        await message.answer(f"Не удалось обновить статус заказа #{order_id}.")
        return

    try:
        await bot.send_message(
            chat_id=order.user_id,
            text=f"Ваш заказ #{order.id} готов! ☕️✨\nЖдём вас ❤️"
        )
        await message.answer(f"Заказ #{order_id} отмечен как выполненный. Пользователь уведомлен.")
    except Exception as e:
        await message.answer(f"Заказ #{order_id} отмечен как выполненный, но не удалось уведомить пользователя: {e}")

# --- Broadcast Handlers ---

@admin_commands_router.message(Command("broadcast"), IsAdminFilter())
async def broadcast_start(message: types.Message, state: FSMContext):
    """
    Starts the broadcast process.
    """
    await state.clear()
    await state.set_state(Broadcast.waiting_for_message)
    await message.answer("Отправьте сообщение, которое вы хотите разослать всем пользователям. "
                         "Вы можете отправить текст, фото с подписью, или просто фото.")

@admin_commands_router.message(Broadcast.waiting_for_message, F.content_type.in_({ContentType.TEXT, ContentType.PHOTO}))
async def broadcast_message_received(message: types.Message, state: FSMContext):
    """
    Receives the message for the broadcast, saves its content to state, and asks for confirmation.
    """
    if message.photo:
        await state.update_data(
            content_type='photo',
            photo_file_id=message.photo[-1].file_id,
            caption=message.caption,
            caption_entities=message.caption_entities
        )
    elif message.text:
        await state.update_data(
            content_type='text',
            text=message.text,
            entities=message.entities
        )
    else:
        await message.answer("Этот тип контента не поддерживается для рассылки.")
        return

    await state.set_state(Broadcast.confirming_broadcast)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_broadcast"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast"),
            ]
        ]
    )
    await message.answer("Вы уверены, что хотите разослать это сообщение всем пользователям?", reply_markup=keyboard)


@admin_commands_router.callback_query(Broadcast.confirming_broadcast, F.data == "cancel_broadcast")
async def broadcast_cancel(callback: types.CallbackQuery, state: FSMContext):
    """
    Cancels the broadcast.
    """
    await state.clear()
    await callback.message.edit_text("Рассылка отменена.")
    await callback.answer()

@admin_commands_router.callback_query(Broadcast.confirming_broadcast, F.data == "confirm_broadcast")
async def broadcast_confirm(callback: types.CallbackQuery, state: FSMContext, bot: Bot, user_service: UserService):
    """
    Confirms and executes the broadcast.
    """
    await callback.message.edit_text("Начинаю рассылку...")
    
    state_data = await state.get_data()
    content_type = state_data.get("content_type")
    
    await state.clear()

    if not content_type:
        await callback.answer("Произошла ошибка: не найдено сообщение для рассылки.", show_alert=True)
        return

    users = await user_service.get_all_users()
    sent_count = 0
    failed_count = 0

    for user in users:
        try:
            if content_type == 'photo':
                await bot.send_photo(
                    chat_id=user.id,
                    photo=state_data['photo_file_id'],
                    caption=state_data.get('caption'),
                    caption_entities=state_data.get('caption_entities')
                )
            elif content_type == 'text':
                await bot.send_message(
                    chat_id=user.id,
                    text=state_data['text'],
                    entities=state_data.get('entities')
                )
            sent_count += 1
            await asyncio.sleep(0.1)
        except Exception:
            failed_count += 1
    
    await callback.message.answer(f"✅ Рассылка завершена!\n\n"
                                f"Успешно отправлено: {sent_count}\n"
                                f"Не удалось отправить: {failed_count}")
    await callback.answer()
