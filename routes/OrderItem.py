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
