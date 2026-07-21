from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from models import (
    get_db,
    Product,
    Order,
    OrderItem,
    OrderItemFieldValue
)

router = APIRouter()


# -----------------------------
# SCHEMAS
# -----------------------------

class FieldValueSchema(BaseModel):
    product_field_id: int
    value: str


class CheckoutItemSchema(BaseModel):
    product_id: int
    quantity: int
    fields: List[FieldValueSchema] = []


class CheckoutSchema(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: str
    items: List[CheckoutItemSchema]


# -----------------------------
# CHECKOUT
# -----------------------------

@router.post("/checkout")
def checkout(data: CheckoutSchema, session=Depends(get_db)):

    total_price = 0

    # Create the Order first
    order = Order(
        customer_name=data.customer_name,
        customer_email=data.customer_email,
        customer_phone=data.customer_phone,
        status="Pending",
        total_price=0
    )

    session.add(order)
    session.flush()          # Generates order.id without committing

    # Loop through every product in the cart
    for item in data.items:

        product = session.query(Product).filter(
            Product.id == item.product_id
        ).first()

        if product is None:
            session.rollback()
            return {
                "message": f"Product with id {item.product_id} not found."
            }

        # Calculate subtotal
        subtotal = product.base_price * item.quantity

        total_price += subtotal

        # Create Order Item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity
        )

        session.add(order_item)
        session.flush()      # Generates order_item.id

        # Save all customer answers
        for field in item.fields:

            answer = OrderItemFieldValue(
                order_item_id=order_item.id,
                product_field_id=field.product_field_id,
                value=field.value
            )

            session.add(answer)

    # Update order total
    order.total_price = total_price

    session.commit()

    session.refresh(order)

    return {
        "message": "Order placed successfully.",
        "order_id": order.id,
        "total_price": order.total_price
    }