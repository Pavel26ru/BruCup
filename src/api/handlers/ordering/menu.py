import os
import json
from datetime import datetime, timedelta
from aiogram import F, Router, Bot, types
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.application.services.option_service import OptionService
from src.application.services.product_service import ProductService
from src.application.services.order_service import OrderService
from src.application.states import Order
from src.application.time_utils import parse_pickup_time, is_valid_pickup_time
from src.api.handlers.admin.actions import AdminActionCallback

# --- CallbackData ---
class LocationCallback(CallbackData, prefix="location"):
    admin_id: int
    address: str

class ProductCallback(CallbackData, prefix="product"):
    id: int

class VolumeCallback(CallbackData, prefix="volume"):
    product_id: int
    volume: str

class OptionCallback(CallbackData, prefix="option"):
    category: str
    item_id: int # 0 for 'skip'

class QuantityCallback(CallbackData, prefix="quantity"):
    count: int

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

@menu_router.callback_query(Order.choosing_location, LocationCallback.filter())
async def cq_select_location(callback: types.CallbackQuery, callback_data: LocationCallback, state: FSMContext, product_service: ProductService):
    await state.update_data(admin_id=callback_data.admin_id, address=callback_data.address)
    await state.set_state(Order.choosing_product)
    
    products = await product_service.get_all_products()
    builder = InlineKeyboardBuilder()
    text = "Наше текущее меню 🌿\nВыберите напиток:"
    for product in products:
        builder.button(text=product.name, callback_data=ProductCallback(id=product.id).pack())
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к выбору кофейни", callback_data="place_order"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@menu_router.callback_query(Order.choosing_product, ProductCallback.filter())
async def cq_select_product(callback: types.CallbackQuery, callback_data: ProductCallback, state: FSMContext, product_service: ProductService):
    await state.set_state(Order.choosing_volume)
    await state.update_data(product_id=callback_data.id)

    product = await product_service.get_product_by_id(callback_data.id)
    if not product:
        await callback.answer("Напиток не найден!", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    text = f"Вы выбрали: {product.name}\n\n"
    for v in product.volumes:
        text += f"{v.volume} - {v.price}₽\n"
    text += "\nВыберите объём:"

    for v in product.volumes:
        builder.button(text=v.volume, callback_data=VolumeCallback(product_id=product.id, volume=v.volume).pack())
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к выбору кофейни", callback_data="place_order"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@menu_router.callback_query(Order.choosing_volume, VolumeCallback.filter())
async def cq_select_volume(callback: types.CallbackQuery, callback_data: VolumeCallback, state: FSMContext, option_service: OptionService):
    await state.set_state(Order.choosing_milk)
    await state.update_data(volume=callback_data.volume)

    milk_options = await option_service.get_options_by_category("milk")
    builder = InlineKeyboardBuilder()
    text = "🥛 Выберите молоко:"

    for option in milk_options:
        builder.button(text=option.name, callback_data=OptionCallback(category="milk", item_id=option.id).pack())
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="Пропустить ➡️", callback_data=OptionCallback(category="milk", item_id=0).pack()))
    user_data = await state.get_data()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к выбору напитка", callback_data=ProductCallback(id=user_data.get("product_id")).pack()))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@menu_router.callback_query(Order.choosing_milk, OptionCallback.filter(F.category == "milk"))
async def cq_select_milk(callback: types.CallbackQuery, callback_data: OptionCallback, state: FSMContext, option_service: OptionService):
    await state.set_state(Order.choosing_syrup)
    await state.update_data(milk_id=callback_data.item_id if callback_data.item_id != 0 else None)

    syrup_options = await option_service.get_options_by_category("syrups")
    builder = InlineKeyboardBuilder()
    text = "🍯 Выберите сироп:"

    for option in syrup_options:
        builder.button(text=option.name, callback_data=OptionCallback(category="syrup", item_id=option.id).pack())
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="Пропустить ➡️", callback_data=OptionCallback(category="syrup", item_id=0).pack()))
    user_data = await state.get_data()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к выбору молока", callback_data=VolumeCallback(product_id=user_data.get("product_id"), volume=user_data.get("volume")).pack()))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@menu_router.callback_query(Order.choosing_syrup, OptionCallback.filter(F.category == "syrup"))
async def cq_select_syrup(callback: types.CallbackQuery, callback_data: OptionCallback, state: FSMContext):
    await state.update_data(syrup_id=callback_data.item_id if callback_data.item_id != 0 else None)
    await state.set_state(Order.choosing_quantity)

    builder = InlineKeyboardBuilder()
    text = "Выберите количество порций:"
    for i in range(1, 4):
        builder.button(text=str(i), callback_data=QuantityCallback(count=i).pack())
    builder.adjust(3)
    user_data = await state.get_data()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к выбору сиропа", callback_data=OptionCallback(category='milk', item_id=user_data.get("milk_id") or 0).pack()))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@menu_router.callback_query(Order.choosing_quantity, QuantityCallback.filter())
async def cq_select_quantity(callback: types.CallbackQuery, callback_data: QuantityCallback, state: FSMContext):
    await state.update_data(quantity=callback_data.count)
    await state.set_state(Order.entering_pickup_time)
    order_time = datetime.now()
    min_ready_time = order_time + timedelta(minutes=10)

    text = (f"На какое время приготовить ваш напиток?\nНапишите ответ сообщением, например: <b>к 08:40</b> или <b>через 10 минут</b>."
            f"\nне ранее {min_ready_time}")
    await callback.message.edit_text(text, parse_mode="HTML")
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
    user_data = await state.get_data()
    builder.row(types.InlineKeyboardButton(text="⬅️ Изменить количество", callback_data=QuantityCallback(count=user_data.get("quantity", 1)).pack()))
    
    await message.answer(summary, reply_markup=builder.as_markup(), parse_mode="HTML")

@menu_router.callback_query(Order.confirming_order, F.data == "confirm_order")
async def cq_confirm_order(callback: types.CallbackQuery, state: FSMContext, bot: Bot, product_service: ProductService, option_service: OptionService, order_service: OrderService):
    user_data = await state.get_data()
    
    # Add user_id to the order data
    user_data['user_id'] = callback.from_user.id

    # Create the order in the database
    try:
        new_order = await order_service.create_order(user_data)
        order_id_for_admin = str(new_order.id)
    except Exception as e:
        # Log the error, maybe notify the user
        await callback.answer("Произошла ошибка при создании заказа. Пожалуйста, попробуйте снова.", show_alert=True)
        # You might want to log 'e' here
        return

    admin_id = user_data.get("admin_id")
    summary_for_admin = await build_order_summary(state, product_service, option_service, order_service)
    
    if admin_id:
        admin_keyboard = InlineKeyboardBuilder()
        admin_keyboard.add(types.InlineKeyboardButton(text="✅ Готов", callback_data=AdminActionCallback(action="done", user_id=callback.from_user.id, order_id=order_id_for_admin).pack()))
        
        await bot.send_message(
            chat_id=admin_id,
            text=f"Новый заказ от @{callback.from_user.username or callback.from_user.id}!\n\n{summary_for_admin}",
            reply_markup=admin_keyboard.as_markup(),
            parse_mode="HTML"
        )
    
    await callback.message.edit_text(f"Ваш заказ #{new_order.id} принят! Мы приготовим его к {user_data.get('pickup_time')}. Как только кофе будет готов - пришлём уведомление.", parse_mode="HTML")
    await callback.answer()
    await state.clear()

@menu_router.callback_query(F.data == "back_to_main_menu")
async def cq_back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Сделать заказ ☕", callback_data="place_order"))
    builder.add(types.InlineKeyboardButton(text="Меню 📖", callback_data="show_menu"))
    builder.add(types.InlineKeyboardButton(text="Режим работы ⏰", callback_data="working_hours"))
    builder.add(types.InlineKeyboardButton(text="Программа лояльности ❤️", callback_data="loyalty_program"))
    builder.adjust(1)
    await callback.message.edit_text("Выберите, что хотите сделать:", reply_markup=builder.as_markup())
    await callback.answer()

@menu_router.callback_query(F.data == "show_menu")
async def show_menu_from_main(callback: types.CallbackQuery):
    await callback.answer("Для просмотра меню, пожалуйста, начните новый заказ через 'Сделать заказ'.", show_alert=True)

@menu_router.callback_query(F.data == "working_hours")
async def cq_working_hours(callback: types.CallbackQuery):
    await callback.answer("Раздел 'Режим работы' в разработке.", show_alert=True)

@menu_router.callback_query(F.data == "loyalty_program")
async def cq_loyalty_program(callback: types.CallbackQuery):
    await callback.answer("Раздел 'Программа лояльности' в разработке.", show_alert=True)