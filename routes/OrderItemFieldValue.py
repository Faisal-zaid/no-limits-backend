from fastapi import APIRouter, Depends
from models import OrderItemFieldValue, get_db
from pydantic import BaseModel

router = APIRouter()

#validation

class OrderItemFieldValueSchema(BaseModel):
    order_item_id: int
    product_field_id: int
    value: str

#create rooute

@router.post("/orderitemfieldvalue")
def create_order_item_field_value(
    data: OrderItemFieldValueSchema,
    session=Depends(get_db)
):

    new_value = OrderItemFieldValue(
        order_item_id=data.order_item_id,
        product_field_id=data.product_field_id,
        value=data.value
    )

    session.add(new_value)

    session.commit()

    session.refresh(new_value)

    return {
        "message": "Order item field value created successfully",
        "order_item_field_value_id": new_value.id
    }