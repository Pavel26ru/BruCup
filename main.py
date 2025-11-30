import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from aiogram.enums import ParseMode
from src.api.routers import main_router
from src.application.services.user_service import UserService
from src.infrastructure.database.repositories.user_repository import InMemoryUserRepository
from src.application.services.product_service import ProductService
from src.infrastructure.database.repositories.product_repository import InMemoryProductRepository
from src.application.services.option_service import OptionService
from src.infrastructure.database.repositories.option_repository import InMemoryOptionRepository

from aiogram.fsm.storage.memory import MemoryStorage

async def main():
    """
    Main function to initialize and start the Telegram bot.
    """
    # Load environment variables from .env file
    load_dotenv()
    TOKEN = os.getenv("TOKEN_BOT")

    if not TOKEN:
        raise ValueError("TOKEN_BOT environment variable not set.")

    # Initialize bot and dispatcher with FSM storage
    storage = MemoryStorage()
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=storage)

    # --- Dependency Injection Setup ---
    user_repository = InMemoryUserRepository()
    user_service = UserService(user_repository=user_repository)

    product_repository = InMemoryProductRepository(file_path="data/menu.json")
    product_service = ProductService(product_repository=product_repository)

    option_repository = InMemoryOptionRepository(file_path="data/options.json")
    option_service = OptionService(option_repository=option_repository)

    from src.application.services.order_service import OrderService
    order_service = OrderService(product_service=product_service, option_service=option_service)

    # Parse coffee shops from .env
    import json
    coffee_shops_json = os.getenv("COFFEE_SHOPS", "[]")
    coffee_shops = json.loads(coffee_shops_json)


    # Register dependencies for handlers
    dp["user_service"] = user_service
    dp["product_service"] = product_service
    dp["option_service"] = option_service
    dp["order_service"] = order_service
    dp["coffee_shops"] = coffee_shops
    # --- End Dependency Injection Setup ---

    # Include routers
    dp.include_router(main_router)

    # Start polling
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")