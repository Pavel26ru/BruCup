import asyncio
import os
import json
import logging
from dotenv import load_dotenv

# --- Load environment variables EARLY ---
load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import text

from aiogram.client.session.aiohttp import AiohttpSession # Keep this import here
from src.api.routers import main_router
from src.application.services.user_service import UserService
from src.infrastructure.database.connection import get_session, async_session_maker
from src.application.services.product_service import ProductService
from src.infrastructure.database.repositories.product_repository import InMemoryProductRepository
from src.application.services.option_service import OptionService
from src.infrastructure.database.repositories.option_repository import InMemoryOptionRepository
from src.application.services.order_service import OrderService


async def warm_up_db(session_maker):
    """
    Performs a simple query to warm up the database connection pool, with retries.
    """
    max_retries = 5
    retry_delay = 5  # seconds
    for attempt in range(max_retries):
        try:
            logging.info(f"Warming up database connection... (Attempt {attempt + 1}/{max_retries})")
            async with session_maker() as session:
                await session.execute(text("SELECT 1"))
            logging.info("Database connection warmed up.")
            return  # Success
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            if attempt < max_retries - 1:
                logging.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logging.error("Could not connect to the database after several retries.")
                raise

async def main():
    """
    Main function to initialize and start the Telegram bot.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('aiogram').setLevel(logging.WARNING) # Suppress noisy aiogram logs

    # --- Load Environment Variables ---
    TOKEN = os.getenv("TOKEN_BOT")
    if not TOKEN:
        raise ValueError("TOKEN_BOT environment variable not set.")
    
    PROXY_URL = os.getenv("PROXY_URL")

    # --- Initialize Services and Repositories ---

    # In-memory services that can be singletons
    product_repository = InMemoryProductRepository(file_path="data/menu.json")
    product_service = ProductService(product_repository=product_repository)

    option_repository = InMemoryOptionRepository(file_path="data/options.json")
    option_service = OptionService(option_repository=option_repository)
    
    # Parse coffee shops from .env
    coffee_shops_json = os.getenv("COFFEE_SHOPS", "[]")
    coffee_shops = json.loads(coffee_shops_json)

    # --- Bot and Dispatcher Setup ---
    # Set up session with proxy if configured
    session_args = {"timeout": 60}
    if PROXY_URL:
        session_args["proxy"] = PROXY_URL
        logging.info(f"Using proxy: {PROXY_URL}")
        
    session = AiohttpSession(**session_args)
    
    # We pass services that don't depend on a DB session directly to the dispatcher
    # They will be available in all handlers
    dp = Dispatcher(
        storage=MemoryStorage(),
        product_service=product_service,
        option_service=option_service,
        coffee_shops=coffee_shops
    )

    # --- Middleware for Database-Dependent Services ---
    class DbSessionMiddleware:
        def __init__(self, session_pool):
            self.session_pool = session_pool

        async def __call__(self, handler, event, data):
            async with self.session_pool() as session:
                data['user_service'] = UserService(session)
                data['order_service'] = OrderService(session, product_service, option_service)
                return await handler(event, data)

    # Register the middleware
    dp.update.outer_middleware.register(DbSessionMiddleware(async_session_maker))
    
    # Include all the routers
    dp.include_router(main_router)

    # Create Bot instance
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML, session=session)

    # Warm up DB connection and start polling
    try:
        await warm_up_db(async_session_maker) # Pass the session_maker
        
        logging.info("Bot started...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
