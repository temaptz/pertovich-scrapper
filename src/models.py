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
    price: Optional[int]
    price_unit: Optional[str]
    qty_available: Optional[int]
    description: Optional[str]
    properties: list[ProductProperty]
    comments: list[str]
    questions: list[ProductQuestion]
