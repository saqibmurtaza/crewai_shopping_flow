from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CartItem(BaseModel):
    product: Dict[str, Any]
    quantity: int = 1

class ShoppingState(BaseModel):
    user_query: str = ""
    search_results: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_products: List[Dict[str, Any]] = Field(default_factory=list)
    previous_results: List[Dict[str, Any]] = Field(default_factory=list)
    cart: List[CartItem] = Field(default_factory=list)
    checkout_status: str = "Not Started"
