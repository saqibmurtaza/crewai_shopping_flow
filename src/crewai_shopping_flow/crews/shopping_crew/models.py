from pydantic import BaseModel
from typing import List, Optional


class Product(BaseModel):
    name: str
    price: float
    category: Optional[str] = None
    description: Optional[str] = None

class SearchResults(BaseModel):
    products: List[Product]
    message: Optional[str] = None

class RecommendationResults(BaseModel):
    recommended_products: List[Product]
    message: Optional[str] = None
    