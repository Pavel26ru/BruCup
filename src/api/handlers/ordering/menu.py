from datetime import datetime, timedelta
from aiogram import F, Router, Bot, types
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.application.services.option_service import OptionService
from src.application.services.product_service import ProductService
from src.application.services.order_service import OrderService
from src.application.states import Order
from src.application.time_utils import parse_pickup_time, is_valid_pickup_time
from src.api.handlers.admin.actions import AdminActionCallback

# --- Category Translations ---
CATEGORY_TRANSLATIONS = {
    "Classic": "Классический кофе",
    "No_coffe": "Не кофе",
    "Alternative": "Альтернатива",
    "Ice_coffe": "Холодный кофе",
    "Signature_coffee": "Авторский кофе",
    "Ice_Tea": "Холодный чай",
    "Signature_Tea": "Авторский чай",
    "Loose_leaf_tea": "Чай листовой",
    "Milkshake": "Молочные коктейли",
    "Protein_shake": "Протеиновые коктейли",
    "Fresh": "Фреш",
    "Lemonade": "Лимонад",
    "Shots": "Шоты"
}

# --- CallbackData ---
class LocationCallback(CallbackData, prefix="location"):
    admin_id: int
    address: str

class CategoryCallback(CallbackData, prefix="category"):
    name: str

class ProductCallback(CallbackData, prefix="product"):
    id: int

class VolumeCallback(CallbackData, prefix="volume"):
    product_id: int
    volume: str

class OptionCallback(CallbackData, prefix="option"):
    category: str
    item_id: int # 0 for 'skip'

class QuantityControlCallback(CallbackData, prefix="q_control"):
    action: str

# --- Router ---
menu_router = Router()

# --- Utility Function ---
async def build_order_summary(state: FSMContext, product_service: ProductService, option_service: OptionService, order_service: OrderService) -> str:
    user_data = await state.get_data()
    product = await product_service.get_product_by_id(user_data.get("product_id"))
    milk = await option_service.get_option_by_id(user_data.get("milk_id")) if user_data.get("milk_id") else None
    syrup = await option_service.get_option_by_id(user_data.get("syrup_id")) if user_data.get("syrup_id") else None
    total_price = await order_service.calculate_total(user_data)
    
    summary = f"<b>Ваш заказ:</b>\n\n"
    if product:
        summary += f"<b>Напиток:</b> {product.name}\n"
    summary += f"<b>Объем:</b> {user_data.get('volume')}\n"
    if milk:
        summary += f"<b>Молоко:</b> {milk.name}\n"
    if syrup:
        summary += f"<b>Сироп:</b> {syrup.name}\n"
    summary += f"<b>Количество:</b> {user_data.get('quantity', 1)} шт.\n"
    if user_data.get('pickup_time'):
        summary += f"<b>Время:</b> {user_data.get('pickup_time')}\n"
    if user_data.get('address'):
        summary += f"<b>Адрес:</b> {user_data.get('address')}\n\n"
    
    summary += f"<b>Итого: {total_price}₽</b>"
    
    return summary

# --- Handlers ---

@menu_router.callback_query(F.data == "place_order")
async def cq_place_order(callback: types.CallbackQuery, state: FSMContext, coffee_shops: list):
    await state.clear()
    await state.set_state(Order.choosing_location)
    builder = InlineKeyboardBuilder()
    text = "Выберите кофейню:"
    for shop in coffee_shops:
        builder.button(text=shop["address"], callback_data=LocationCallback(admin_id=shop["admin_id"], address=shop["address"]).pack())
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_menu"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@menu_router.callback_query(F.data == "working_hours")
async def cq_working_hours(callback: types.CallbackQuery):
    await callback.answer(
        "Мы работаем для вас ежедневно с 7:00 до 23:00, без перерывов и выходных!",
        show_alert=True
    )

@menu_router.callback_query(F.data == "back_to_main_menu")
async def cq_back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    welcome_message = "Выберите, что хотите сделать:"
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Сделать заказ ☕", callback_data="place_order"))
    builder.add(types.InlineKeyboardButton(text="Меню 📖", callback_data="show_menu"))
    builder.add(types.InlineKeyboardButton(text="Режим работы ⏰", callback_data="working_hours"))
    builder.add(types.InlineKeyboardButton(text="Программа лояльности ❤️", callback_data="loyalty_program"))
    builder.adjust(1)
    await callback.message.edit_text(
        welcome_message,
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@menu_router.callback_query(Order.choosing_location, LocationCallback.filter())
async def cq_select_location(callback: types.CallbackQuery, callback_data: LocationCallback, state: FSMContext, product_service: ProductService):
    await state.update_data(admin_id=callback_data.admin_id, address=callback_data.address)
    await state.set_state(Order.choosing_category)
    categories = await product_service.get_categories()
    builder = InlineKeyboardBuilder()
    text = "Наше меню 🌿\nВыберите категорию:"
    for category_name in categories:
        translated_name = CATEGORY_TRANSLATIONS.get(category_name, category_name)
        builder.button(text=translated_name, callback_data=CategoryCallback(name=category_name).pack())
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к выбору кофейни", callback_data="place_order"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# This is the "Back to Categories" button handler
@menu_router.callback_query(F.data == "back_to_categories")
async def cq_back_to_categories(callback: types.CallbackQuery, state: FSMContext, product_service: ProductService):
    # This handler essentially does the same as cq_select_location, but without needing its callback_data
    await state.set_state(Order.choosing_category)
    await state.update_data(category=None, product_id=None, volume=None, milk_id=None, syrup_id=None, quantity=None)
    
    categories = await product_service.get_categories()
    builder = InlineKeyboardBuilder()
    text = "Наше меню 🌿\nВыберите категорию:"
    for category_name in categories:
        translated_name = CATEGORY_TRANSLATIONS.get(category_name, category_name)
        builder.button(text=translated_name, callback_data=CategoryCallback(name=category_name).pack())
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к выбору кофейни", callback_data="place_order"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@menu_router.callback_query(Order.choosing_category, CategoryCallback.filter())
async def cq_select_category(callback: types.CallbackQuery, callback_data: CategoryCallback, state: FSMContext, product_service: ProductService):
    await state.update_data(category=callback_data.name, product_id=None, volume=None, milk_id=None, syrup_id=None, quantity=None)
    await state.set_state(Order.choosing_product)
    
    products = await product_service.get_products_by_category(callback_data.name)
    builder = InlineKeyboardBuilder()
    translated_category_name = CATEGORY_TRANSLATIONS.get(callback_data.name, callback_data.name)
    text = f"Категория: <b>{translated_category_name}</b>\nВыберите напиток:"
    for product in products:
        builder.button(text=product.name, callback_data=ProductCallback(id=product.id).pack())
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к выбору категории", callback_data="back_to_categories"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@menu_router.callback_query(Order.choosing_product, ProductCallback.filter())
async def cq_select_product(callback: types.CallbackQuery, callback_data: ProductCallback, state: FSMContext, product_service: ProductService, option_service: OptionService):
    await state.set_state(Order.choosing_volume)
    await state.update_data(product_id=callback_data.id, volume=None, milk_id=None, syrup_id=None, quantity=None)

    product = await product_service.get_product_by_id(callback_data.id)
    if not product:
        await callback.answer("Напиток не найден!", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    text = f"Вы выбрали: {product.name}\n\n"
    # Check if there are any volumes to select
    if product.volumes and any(v.volume for v in product.volumes):
        text += "Выберите объём:"
        for v in product.volumes:
            builder.button(text=f"{v.volume} - {v.price}₽", callback_data=VolumeCallback(product_id=product.id, volume=v.volume).pack())
        builder.adjust(1)
        builder.row(types.InlineKeyboardButton(text="⬅️ Назад к выбору напитка", callback_data="back_to_products"))
    else: # If no volumes, skip to milk selection
        await state.update_data(volume='default')
        await cq_select_volume(callback, VolumeCallback(product_id=product.id, volume='default'), state, option_service)
        return

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
    
# Handler for the "Back to Product List" button
@menu_router.callback_query(F.data == "back_to_products")
async def cq_back_to_products(callback: types.CallbackQuery, state: FSMContext, product_service: ProductService):
    user_data = await state.get_data()
    category_name = user_data.get("category")
    await cq_select_category(callback, CategoryCallback(name=category_name), state, product_service)


@menu_router.callback_query(Order.choosing_volume, VolumeCallback.filter())
async def cq_select_volume(callback: types.CallbackQuery, callback_data: VolumeCallback, state: FSMContext, option_service: OptionService):
    await state.set_state(Order.choosing_milk)
    await state.update_data(volume=callback_data.volume, milk_id=None, syrup_id=None, quantity=None)
    
    milk_options = await option_service.get_options_by_category("milk")
    builder = InlineKeyboardBuilder()
    text = "🥛 Выберите молоко:"
    for option in milk_options:
        builder.button(text=f"{option.name} (+{option.price}₽)", callback_data=OptionCallback(category="milk", item_id=option.id).pack())
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="Пропустить ➡️", callback_data=OptionCallback(category="milk", item_id=0).pack()))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к выбору объёма", callback_data="back_to_volume"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# Handler for the "Back to Volume" button
@menu_router.callback_query(F.data == "back_to_volume")
async def cq_back_to_volume(callback: types.CallbackQuery, state: FSMContext, product_service: ProductService, option_service: OptionService):
    user_data = await state.get_data()
    product_id = user_data.get("product_id")
    await cq_select_product(callback, ProductCallback(id=product_id), state, product_service, option_service)


@menu_router.callback_query(Order.choosing_milk, OptionCallback.filter(F.category == "milk"))
async def cq_select_milk(callback: types.CallbackQuery, callback_data: OptionCallback, state: FSMContext, option_service: OptionService):
    await state.set_state(Order.choosing_syrup)
    await state.update_data(milk_id=callback_data.item_id if callback_data.item_id != 0 else None, syrup_id=None, quantity=None)

    syrup_options = await option_service.get_options_by_category("syrups")
    builder = InlineKeyboardBuilder()
    text = "🍯 Выберите сироп:"
    for option in syrup_options:
        builder.button(text=f"{option.name} (+{option.price}₽)", callback_data=OptionCallback(category="syrup", item_id=option.id).pack())
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="Пропустить ➡️", callback_data=OptionCallback(category="syrup", item_id=0).pack()))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к выбору молока", callback_data="back_to_milk"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# Handler for the "Back to Milk" button
@menu_router.callback_query(F.data == "back_to_milk")
async def cq_back_to_milk(callback: types.CallbackQuery, state: FSMContext, option_service: OptionService):
    user_data = await state.get_data()
    # Re-call cq_select_volume to show the milk options again
    await cq_select_volume(callback, VolumeCallback(product_id=user_data.get("product_id"), volume=user_data.get("volume")), state, option_service)


async def show_quantity_selection(callback: types.CallbackQuery, state: FSMContext):
    """
    Displays the quantity selection interface.
    """
    user_data = await state.get_data()
    quantity = user_data.get("quantity", 1)

    text = "Выберите количество порций:"
    builder = InlineKeyboardBuilder()
    
    builder.button(text="-", callback_data=QuantityControlCallback(action="minus").pack())
    builder.button(text=str(quantity), callback_data="ignore") # Just for display
    builder.button(text="+", callback_data=QuantityControlCallback(action="plus").pack())
    
    builder.row(types.InlineKeyboardButton(text="✅ Далее", callback_data="quantity_confirm"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к выбору сиропа", callback_data="back_to_syrup"))
    
    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    except TelegramBadRequest:
        pass # Ignore "message is not modified" error
    
    await callback.answer()


@menu_router.callback_query(Order.choosing_syrup, OptionCallback.filter(F.category == "syrup"))
async def cq_select_syrup(callback: types.CallbackQuery, callback_data: OptionCallback, state: FSMContext):
    await state.update_data(syrup_id=callback_data.item_id if callback_data.item_id != 0 else None, quantity=1)
    await state.set_state(Order.choosing_quantity)
    await show_quantity_selection(callback, state)


@menu_router.callback_query(Order.choosing_quantity, QuantityControlCallback.filter())
async def cq_change_quantity(callback: types.CallbackQuery, callback_data: QuantityControlCallback, state: FSMContext):
    user_data = await state.get_data()
    quantity = user_data.get("quantity", 1)

    if callback_data.action == "plus":
        quantity += 1
    elif callback_data.action == "minus" and quantity > 1:
        quantity -= 1

    await state.update_data(quantity=quantity)
    await show_quantity_selection(callback, state)


# Handler for the "Back to Syrup" button
@menu_router.callback_query(Order.choosing_quantity, F.data == "back_to_syrup")
async def cq_back_to_syrup(callback: types.CallbackQuery, state: FSMContext, option_service: OptionService):
    await state.set_state(Order.choosing_syrup)
    
    syrup_options = await option_service.get_options_by_category("syrups")
    builder = InlineKeyboardBuilder()
    text = "🍯 Выберите сироп:"
    for option in syrup_options:
        builder.button(text=f"{option.name} (+{option.price}₽)", callback_data=OptionCallback(category="syrup", item_id=option.id).pack())
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="Пропустить ➡️", callback_data=OptionCallback(category="syrup", item_id=0).pack()))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к выбору молока", callback_data="back_to_milk"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@menu_router.callback_query(Order.choosing_quantity, F.data == "quantity_confirm")
async def cq_confirm_quantity(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(pickup_time=None)
    await state.set_state(Order.entering_pickup_time)
    order_time = datetime.now()
    min_ready_time = order_time + timedelta(minutes=10)
    text = (f"На какое время приготовить ваш напиток?\nНапишите ответ сообщением, например: <b>к 08:40</b> или <b>через 10 минут</b>."
            f"\nне ранее {min_ready_time.strftime('%H:%M')}")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=None)
    await callback.answer()


@menu_router.message(Order.entering_pickup_time)
async def handle_pickup_time(message: types.Message, state: FSMContext, product_service: ProductService, option_service: OptionService, order_service: OrderService):
    pickup_time = parse_pickup_time(message.text)
    if not pickup_time or not is_valid_pickup_time(pickup_time):
        await message.answer("Это слишком быстро или неверный формат! Мы не успеем.\nМинимальное время ожидания - 10 минут. Пожалуйста, выберите другое время (например, 'через 20 минут').", parse_mode="HTML")
        return

    await state.update_data(pickup_time=pickup_time.strftime("%H:%M"))
    await state.set_state(Order.confirming_order)
    
    summary = await build_order_summary(state, product_service, option_service, order_service)
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="confirm_order"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Изменить количество", callback_data="back_to_quantity"))
    
    await message.answer(summary, reply_markup=builder.as_markup(), parse_mode="HTML")

# Handler for "Back to Quantity"
@menu_router.callback_query(F.data == "back_to_quantity")
async def cq_back_to_quantity(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Order.choosing_quantity)
    await show_quantity_selection(callback, state)


@menu_router.callback_query(Order.confirming_order, F.data == "confirm_order")
async def cq_confirm_order(callback: types.CallbackQuery, state: FSMContext, bot: Bot, order_service: OrderService, product_service: ProductService, option_service: OptionService):
    """
    Handles the final order confirmation.
    Creates the order, notifies the admin, confirms to the user, and clears state.
    """
    user_data = await state.get_data()
    user_id = callback.from_user.id
    admin_id = user_data.get("admin_id")

    if not admin_id:
        await callback.answer("Ошибка: не удалось найти администратора для этой кофейни.", show_alert=True)
        return

    # Create order in the database
    full_order_data = {**user_data, "user_id": user_id}
    new_order = await order_service.create_order(full_order_data)

    # Notify user
    await callback.message.edit_text(
        f"✅ Ваш заказ #{new_order.id} принят!\n\n"
        f"Мы начнем готовить его к указанному времени ({new_order.pickup_time}). "
        f"Вы получите уведомление, когда все будет готово."
    )

    # Build summary for admin
    order_summary_for_admin = await build_order_summary(state, product_service, option_service, order_service)
    
    admin_message = (
        f"🔔 <b>Новый заказ #{new_order.id}</b> 🔔\n\n"
        f"{order_summary_for_admin}\n\n"
        f"👤 <b>Клиент:</b> {callback.from_user.full_name} (@{callback.from_user.username or 'N/A'})")

    # Build keyboard for admin
    admin_keyboard = InlineKeyboardBuilder()
    admin_keyboard.add(types.InlineKeyboardButton(
        text="✅ Готово",
        callback_data=AdminActionCallback(action="done", user_id=user_id, order_id=new_order.id).pack()
    ))
    
    # Notify admin
    await bot.send_message(
        chat_id=admin_id,
        text=admin_message,
        reply_markup=admin_keyboard.as_markup(),
        parse_mode="HTML"
    )

    # Clear state
    await state.clear()
    await callback.answer("Заказ подтвержден!")
