from fastapi import APIRouter, Depends
from models import OrderItem, get_db
from pydantic import BaseModel

router = APIRouter()

#validation

class OrderItemSchema(BaseModel):
    order_id: int
    product_id: int
    quantity: int