from typing import Optional
from pydantic import BaseModel


class ProductQuestion(BaseModel):
    question: str
    answer: str

class ProductProperty(BaseModel):
    label: str
    value: str


class Product(BaseModel):
    url: str
    name: Optional[str]
    price: Optional[float]
    unit: Optional[str]
    qty_available: Optional[int]
    description: Optional[str]
    properties: list[ProductProperty]
    comments: list[str]
    questions: list[ProductQuestion]


class Catalog(BaseModel):
    products: list[Product]