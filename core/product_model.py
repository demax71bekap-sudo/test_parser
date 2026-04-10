from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime


@dataclass
class Product:
    """Модель данных товара"""
    article: str
    name: str
    price: float
    detail_url: str
    source: str
    category: str = ""
    description: str = ""
    specs: Dict[str, str] = field(default_factory=dict)
    image_url: str = ""
    image_path: str = ""
    status: str = "pending"
    error_message: Optional[str] = None
    retries: int = 0
    parsed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Конвертация в словарь для JSON"""
        return {
            "article": self.article,
            "name": self.name,
            "price": self.price,
            "detail_url": self.detail_url,
            "source": self.source,
            "category": self.category,
            "description": self.description,
            "specs": self.specs,
            "image_url": self.image_url,
            "image_path": self.image_path,
            "status": self.status,
            "error_message": self.error_message,
            "retries": self.retries,
            "parsed_at": self.parsed_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Product':
        """Создание из словаря"""
        return cls(**data)