from fastapi import APIRouter, Depends
from models import OrderItemFieldValue, get_db
from pydantic import BaseModel

router = APIRouter()

#validation

class OrderItemFieldValueSchema(BaseModel):
    order_item_id: int
    product_field_id: int
    value: str