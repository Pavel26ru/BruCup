import re
from datetime import datetime, timedelta

def parse_pickup_time(text: str) -> datetime | None:
    """
    Parses user input to determine the pickup time.
    Handles formats like "к 08:40" and "через 10 минут".

    Args:
        text (str): The user's input text.

    Returns:
        datetime | None: The parsed datetime object, or None if parsing fails.
    """
    now = datetime.now()

    # Case 1: "через N минут" (in N minutes)
    match = re.search(r"через (\d+)", text, re.IGNORECASE)
    if match:
        minutes = int(match.group(1))
        return now + timedelta(minutes=minutes)

    # Case 2: "к HH:MM" (at HH:MM)
    match = re.search(r"(\d{1,2}):(\d{2})", text)
    if match:
        hours, minutes = int(match.group(1)), int(match.group(2))
        try:
            pickup_dt = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
            if pickup_dt < now:
                # If the specified time is in the past, assume it's for the next day
                pickup_dt += timedelta(days=1)
            return pickup_dt
        except ValueError:
            return None

    return None

def is_valid_pickup_time(pickup_time: datetime) -> bool:
    """
    Checks if the pickup time is at least 10 minutes from now.

    Args:
        pickup_time (datetime): The proposed pickup time.

    Returns:
        bool: True if the time is valid, False otherwise.
    """
    return pickup_time >= (datetime.now() + timedelta(minutes=10))

