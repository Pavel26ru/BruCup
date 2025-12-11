from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from src.application.services.user_service import UserService

# Create a router for handling start command and general user interactions
start_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: types.Message, user_service: UserService):
    """
    Handles the /start command.
    Registers or retrieves the user, and sends a welcome message with the appropriate menu (admin or user).
    """
    user_data = message.from_user
    if not user_data:
        # This case should ideally not happen for a /start command from a user
        await message.answer("Произошла ошибка при получении ваших данных.")
        return

    # Get or create user in the database
    user = await user_service.get_or_create_user(
        user_id=user_data.id,
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )

    welcome_message = (
        f"Привет, {user.first_name}! 👋\n"
        "Вы в кофейне <b>Bru Cup</b>.\n" # Placeholder for coffee shop name
    )

    if user and user.is_admin:
        welcome_message += "Добро пожаловать в админ-панель!"
        admin_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="/orders")],
                [KeyboardButton(text="/done"), KeyboardButton(text="/broadcast")],
                [KeyboardButton(text="/menu_edit")],
            ],
            resize_keyboard=True
        )
        await message.answer(welcome_message, reply_markup=admin_keyboard)
    else:
        welcome_message += "Здесь можно заказать кофе заранее — мы приготовим его к вашему приходу!\n\n"
        welcome_message += "Выберите, что хотите сделать:"
        # Build the inline keyboard for the main menu
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="Сделать заказ ☕", callback_data="place_order"))
        builder.add(types.InlineKeyboardButton(text="Меню 📖", callback_data="show_menu"))
        builder.add(types.InlineKeyboardButton(text="Режим работы ⏰", callback_data="working_hours"))
        builder.add(types.InlineKeyboardButton(text="Программа лояльности ❤️", callback_data="loyalty_program"))
        builder.adjust(1) # Display buttons in a single column

        await message.answer(
            welcome_message,
            reply_markup=builder.as_markup()
        )
