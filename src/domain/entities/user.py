from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    """
    Represents a user of the Telegram bot.

    Attributes:
        id (int): Unique identifier for the user (Telegram user ID).
        username (str | None): Telegram username of the user. Can be None.
        first_name (str): First name of the user.
        last_name (str | None): Last name of the user. Can be None.
        is_admin (bool): True if the user has admin privileges, False otherwise.
        created_at (datetime): Timestamp when the user record was created.
        updated_at (datetime): Timestamp when the user record was last updated.
    """
    id: int
    username: str | None
    first_name: str
    last_name: str | None
    is_admin: bool = False
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    def to_dict(self):
        """Converts the User object to a dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict):
        """Creates a User object from a dictionary."""
        return User(
            id=data["id"],
            username=data.get("username"),
            first_name=data["first_name"],
            last_name=data.get("last_name"),
            is_admin=data.get("is_admin", False),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
        )
