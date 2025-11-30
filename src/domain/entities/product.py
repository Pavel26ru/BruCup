from dataclasses import dataclass
from typing import List

@dataclass
class Volume:
    """
    Represents a volume option for a product.

    Attributes:
        volume (str): The volume description (e.g., "250мл").
        price (int): The price for this volume.
    """
    volume: str
    price: int

@dataclass
class Product:
    """
    Represents a product from the menu.

    Attributes:
        id (int): Unique identifier for the product.
        name (str): The name of the product (e.g., "Капучино").
        volumes (List[Volume]): A list of available volumes and their prices.
    """
    id: int
    name: str
    volumes: List[Volume]

    def to_dict(self):
        """Converts the Product object to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "volumes": [{"volume": v.volume, "price": v.price} for v in self.volumes],
        }

    @staticmethod
    def from_dict(data: dict):
        """Creates a Product object from a dictionary."""
        return Product(
            id=data["id"],
            name=data["name"],
            volumes=[Volume(volume=v["volume"], price=v["price"]) for v in data["volumes"]],
        )
