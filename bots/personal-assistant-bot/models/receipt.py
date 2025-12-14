"""
Модели чека и товаров
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Listfrom utils.timezone import now_naive as moscow_now

@dataclass
class ReceiptItem:
    """Модель товара в чеке"""
    
    id: str
    receipt_id: str
    item_name: str
    category: str = 'Прочее'
    price: float = 0.0
    quantity: float = 1.0
    unit: Optional[str] = None
    price_per_unit: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ReceiptItem':
        return cls(
            id=data.get('id', ''),
            receipt_id=data.get('receipt_id', ''),
            item_name=data.get('item_name', ''),
            category=data.get('category', 'Прочее'),
            price=data.get('price', 0.0),
            quantity=data.get('quantity', 1.0),
            unit=data.get('unit'),
            price_per_unit=data.get('price_per_unit')
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'receipt_id': self.receipt_id,
            'item_name': self.item_name,
            'category': self.category,
            'price': self.price,
            'quantity': self.quantity,
            'unit': self.unit,
            'price_per_unit': self.price_per_unit
        }


@dataclass
class Receipt:
    """Модель чека"""
    
    id: str
    user_id: str
    store_name: Optional[str] = None
    store_location: Optional[str] = None
    receipt_date: Optional[datetime] = None
    total_sum: float = 0.0
    file_url: Optional[str] = None
    created_at: datetime = field(default_factory=moscow_now)
    metadata: dict = field(default_factory=dict)
    
    # Связанные товары
    items: List[ReceiptItem] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Receipt':
        items = [ReceiptItem.from_dict(i) for i in data.get('items', [])]
        
        return cls(
            id=data.get('id', ''),
            user_id=data.get('user_id', ''),
            store_name=data.get('store_name'),
            store_location=data.get('store_location'),
            receipt_date=data.get('receipt_date'),
            total_sum=data.get('total_sum', 0.0),
            file_url=data.get('file_url'),
            created_at=data.get('created_at', moscow_now()),
            metadata=data.get('metadata', {}),
            items=items
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'store_name': self.store_name,
            'store_location': self.store_location,
            'receipt_date': self.receipt_date.isoformat() if isinstance(self.receipt_date, datetime) else self.receipt_date,
            'total_sum': self.total_sum,
            'file_url': self.file_url,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'metadata': self.metadata
        }
    
    @property
    def items_count(self) -> int:
        return len(self.items)
    
    @property
    def categories(self) -> List[str]:
        return list(set(item.category for item in self.items))
