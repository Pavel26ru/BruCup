from aiogram import Router
from src.api.handlers.ordering.start import start_router
from src.api.handlers.ordering.menu import menu_router
from src.api.handlers.admin.actions import admin_router

# Main router for the bot
main_router = Router()

# Include other routers here
main_router.include_router(start_router)
main_router.include_router(menu_router)
main_router.include_router(admin_router)
