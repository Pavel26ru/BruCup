from aiogram.filters import Filter
from aiogram.types import Message
from src.application.services.user_service import UserService

class IsAdminFilter(Filter):
    """
    Custom filter to check if a user is an administrator.
    """
    async def __call__(self, message: Message, user_service: UserService) -> bool:
        user = await user_service.get_user_by_id(message.from_user.id)
        return user is not None and user.is_admin
