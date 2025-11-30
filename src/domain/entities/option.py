from dataclasses import dataclass

@dataclass
class Option:
    """
    Represents a selectable option for a product, such as milk or syrup.

    Attributes:
        id (int): Unique identifier for the option.
        name (str): The name of the option (e.g., "Овсяное").
        price (int): The price of the option.
        category (str): The category of the option (e.g., "milk", "syrup").
    """
    id: int
    name: str
    price: int
    category: str

    def to_dict(self):
        """Converts the Option object to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
        }

    @staticmethod
    def from_dict(data: dict, category: str):
        """Creates an Option object from a dictionary and category."""
        return Option(
            id=data["id"],
            name=data["name"],
            price=data["price"],
            category=category,
        )
