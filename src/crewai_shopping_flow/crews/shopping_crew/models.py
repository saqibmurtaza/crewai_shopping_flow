from pydantic import BaseModel
from typing import List

class Product(BaseModel):
    name: str
    price: float
    description: str = ""

class SearchResults(BaseModel):
    products: List[Product]
    message: str = "" 