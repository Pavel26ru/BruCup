from aiogram import F, Router, Bot, types
from aiogram.filters.callback_data import CallbackData
from aiogram.exceptions import TelegramBadRequest
from src.application.services.order_service import OrderService

# This needs to be defined here or imported from a central place
# to be recognized by the filter. Let's define it here for now.
class AdminActionCallback(CallbackData, prefix="admin"):
    action: str
    user_id: int
    order_id: int

admin_router = Router()

@admin_router.callback_query(AdminActionCallback.filter(F.action == "done"))
async def cq_admin_order_done(callback: types.CallbackQuery, callback_data: AdminActionCallback, bot: Bot, order_service: OrderService):
    """
    Handles the 'Done' button press from the admin chat.
    Updates the database, edits the admin message, and notifies the user.
    """
    # 0. Update order status in the database
    try:
        completed_order = await order_service.complete_order(callback_data.order_id)
        if not completed_order:
            await callback.answer(f"Заказ с ID {callback_data.order_id} не найден.", show_alert=True)
            return
    except Exception as e:
        await callback.answer(f"Не удалось обновить статус заказа: {e}", show_alert=True)
        return

    # 1. Edit the message to show it's completed and remove the button
    try:
        await callback.message.edit_text(
            text=f"{callback.message.text}\n\n<b>✅ Заказ выполнен!</b>",
            reply_markup=None, # Remove keyboard
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" in e.message:
            await callback.answer("Заказ уже был отмечен как выполненный.")
            return
        else:
            await callback.answer(f"Произошла ошибка: {e.message}", show_alert=True)
            return

    # 2. Notify the user that their order is ready.
    try:
        await bot.send_message(
            chat_id=callback_data.user_id,
            text="Ваш кофе готов! ☕️✨\nЖдём вас ❤️"
        )
    except Exception as e:
        await callback.answer(f"Не удалось уведомить пользователя: {e}", show_alert=True)
        return

    # 3. Answer the callback query to remove the loading animation.
    try:
        await callback.answer("Заказ отмечен как выполненный.")
    except TelegramBadRequest:
        pass
