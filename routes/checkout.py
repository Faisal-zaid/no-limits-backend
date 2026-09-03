from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List

from models import (
    get_db,
    Product,
    Order,
    OrderItem,
    OrderItemFieldValue
)

router = APIRouter()


class FieldValueSchema(BaseModel):
    product_field_id: int
    value: str


class CheckoutItemSchema(BaseModel):
    product_id: int
    quantity: int
    fields: List[FieldValueSchema] = Field(default_factory=list)


class CheckoutSchema(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: str
    items: List[CheckoutItemSchema]


@router.post("/checkout")
def checkout(
    data: CheckoutSchema,
    session=Depends(get_db)
):

    # 1. Make sure cart isn't empty
    if not data.items:
        raise HTTPException(
            status_code=400,
            detail="Your cart is empty."
        )

    total_price = 0
    products = {}

    # 
    # 2. CHECK PRODUCTS AND STOCK FIRST
    # 

    for item in data.items:

        if item.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be greater than zero."
            )

        product = (
            session.query(Product)
            .filter(Product.id == item.product_id)
            .first()
        )

        if product is None:
            raise HTTPException(
                status_code=404,
                detail=f"Product with id {item.product_id} not found."
            )

        # Check stock
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Not enough stock for {product.name}. "
                    f"Available: {product.stock}, "
                    f"requested: {item.quantity}."
                )
            )

        if product.base_price is None:
            raise HTTPException(
                status_code=400,
                detail=f"Product '{product.name}' has no price."
            )

        products[item.product_id] = product

        subtotal = product.base_price * item.quantity
        total_price += subtotal


    
    # 3. CREATE THE ORDER
    

    order = Order(
        customer_name=data.customer_name,
        customer_email=data.customer_email,
        customer_phone=data.customer_phone,
        status="Pending",
        total_price=total_price
    )

    session.add(order)
    session.flush()


    
    # 4. CREATE ORDER ITEMS AND REDUCE STOCK
    

    for item in data.items:

        product = products[item.product_id]

        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity
        )

        session.add(order_item)
        session.flush()


        # Save custom field values
        for field in item.fields:

            answer = OrderItemFieldValue(
                order_item_id=order_item.id,
                product_field_id=field.product_field_id,
                value=field.value
            )

            session.add(answer)


        # REDUCE PRODUCT STOCK
        product.stock -= item.quantity


    # -----------------------------------------
    # 5. SAVE EVERYTHING
    # -----------------------------------------

    try:
        session.commit()

    except Exception:
        session.rollback()

        raise HTTPException(
            status_code=500,
            detail="Could not complete checkout."
        )


    session.refresh(order)


    
    #  RETURN RESULT
    

    return {
        "message": "Order placed successfully.",
        "order_id": order.id,
        "total_price": order.total_price,
        "status": order.status
    }