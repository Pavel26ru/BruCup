import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from aiogram import Bot, Dispatcher

from aiogram.enums import ParseMode
from src.api.routers import main_router
from src.application.services.user_service import UserService
from src.infrastructure.database.connection import get_session
# No direct import of SQLAlchemyUserRepository needed here anymore
# No direct import of SQLAlchemyOrderRepository needed here anymore
from src.application.services.product_service import ProductService
from src.infrastructure.database.repositories.product_repository import InMemoryProductRepository # Still in-memory
from src.application.services.option_service import OptionService
from src.infrastructure.database.repositories.option_repository import InMemoryOptionRepository # Still in-memory

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

    # --- Dependency Injection Setup with Session Middleware ---
    # Product and Option services are still in-memory and don't need the session directly
    product_repository = InMemoryProductRepository(file_path="data/menu.json")
    product_service = ProductService(product_repository=product_repository)

    option_repository = InMemoryOptionRepository(file_path="data/options.json")
    option_service = OptionService(option_repository=option_repository)
    
    # Parse coffee shops from .env
    import json
    coffee_shops_json = os.getenv("COFFEE_SHOPS", "[]")
    coffee_shops = json.loads(coffee_shops_json)

    # Outer middleware to inject services per request
    @dp.update.outer_middleware()
    async def services_middleware(handler, event, data):
        async for session in get_session(): # Get a new session for each request
            from src.application.services.order_service import OrderService # Import inside middleware
            # Services that use the DB
            data["user_service"] = UserService(session)
            data["order_service"] = OrderService(session, product_service, option_service)
            
            # Services that don't use the DB directly
            data["product_service"] = product_service
            data["option_service"] = option_service
            data["coffee_shops"] = coffee_shops
            
            return await handler(event, data)

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