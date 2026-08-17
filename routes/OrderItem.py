from fastapi import APIRouter, Depends
from models import OrderItem, get_db
from pydantic import BaseModel

router = APIRouter()

#validation

class OrderItemSchema(BaseModel):
    order_id: int
    product_id: int
    quantity: int

# create order item

@router.post("/orderitem")
def create_order_item(
    item: OrderItemSchema,
    session=Depends(get_db)
):
    # Create the order item
    new_order_item = OrderItem(
        order_id=item.order_id,
        product_id=item.product_id,
        quantity=item.quantity
    )

    # Add it to the transaction
    session.add(new_order_item)

    # Save to database
    session.commit()

    # Get the generated ID
    session.refresh(new_order_item)

    return {
        "message": "Order item created successfully",
        "order_item_id": new_order_item.id
    }

#get all orderitems

@router.get("/orderitem")
def get_order_items(session=Depends(get_db)):

    order_items = session.query(OrderItem).all()

    return order_items

#get order items for a specific order

@router.get("/orderitem/order/{order_id}")
def get_order_items_by_order(
    order_id: int,
    session=Depends(get_db)
):

    order_items = (
        session.query(OrderItem)
        .filter(OrderItem.order_id == order_id)
        .all()
    )

    return order_items

#get one order item

@router.get("/orderitem/{order_item_id}")
def get_order_item(
    order_item_id: int,
    session=Depends(get_db)
):

    order_item = (
        session.query(OrderItem)
        .filter(OrderItem.id == order_item_id)
        .first()
    )

    if not order_item:
        return {
            "message": "Order item not found"
        }

    return order_item

