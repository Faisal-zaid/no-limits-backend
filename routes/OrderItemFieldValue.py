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

#get all items

@router.get("/orderitemfieldvalue")
def get_order_item_field_values(
    session=Depends(get_db)
):

    values = session.query(
        OrderItemFieldValue
    ).all()

    return values

# GET ONE ORDER ITEM FIELD VALUE

@router.get("/orderitemfieldvalue/{value_id}")
def get_order_item_field_value(
    value_id: int,
    session=Depends(get_db)
):

    value = session.query(
        OrderItemFieldValue
    ).filter(
        OrderItemFieldValue.id == value_id
    ).first()

    if not value:
        return {
            "message": "Order item field value not found"
        }

    return value

#get one item

@router.get("/orderitemfieldvalue/orderitem/{order_item_id}")
def get_values_by_order_item(
    order_item_id: int,
    session=Depends(get_db)
):

    values = session.query(
        OrderItemFieldValue
    ).filter(
        OrderItemFieldValue.order_item_id == order_item_id
    ).all()

    return values

# UPDATE ORDER ITEM FIELD VALUE

@router.patch("/orderitemfieldvalue/{value_id}")
def update_order_item_field_value(
    value_id: int,
    data: OrderItemFieldValueSchema,
    session=Depends(get_db)
):

    value = session.query(
        OrderItemFieldValue
    ).filter(
        OrderItemFieldValue.id == value_id
    ).first()

    if not value:
        return {
            "message": "Order item field value not found"
        }

    value.order_item_id = data.order_item_id
    value.product_field_id = data.product_field_id
    value.value = data.value

    session.commit()

    session.refresh(value)

    return {
        "message": "Order item field value updated successfully"
    }

#delte items

@router.delete("/orderitemfieldvalue/{value_id}")
def delete_order_item_field_value(
    value_id: int,
    session=Depends(get_db)
):

    value = session.query(
        OrderItemFieldValue
    ).filter(
        OrderItemFieldValue.id == value_id
    ).first()

    if not value:
        return {
            "message": "Order item field value not found"
        }

    session.delete(value)

    session.commit()

    return {
        "message": "Order item field value deleted successfully"
    }