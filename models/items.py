from dataclasses import dataclass, field   
from typing import Literal

import uuid

@dataclass
class RolimonsData:
    rap: int
    value: int
    
@dataclass
class BuyData:
    collectible_item_id: str
    collectible_item_instance_id: str
    collectible_product_id: str

    expected_price: int
    expected_purchaser_id: str
    
    expected_seller_id: int = 1
    expected_purchaser_type: str = "User"
    expected_currency: int = 1
    expected_seller_type: Literal[None] = None
    
    idempotency_key: str = field(default_factory=lambda: str(uuid.uuid4()))
    
@dataclass
class Data:
    item_id: int
    product_id: int
    collectible_item_id: str
    
    lowest_resale_price: int
    
@dataclass
class Generic:
    item_id: int
    collectible_item_id: str