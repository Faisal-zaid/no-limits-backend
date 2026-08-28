from fastapi import APIRouter, Depends #the APIRouter allows us to use routes easily than relying everything in app.py
from models import Order, get_db
from pydantic import BaseModel

router=APIRouter()

#for validation of Order i will do 
class OrderSchema(BaseModel):
    customer_name:str
    customer_email:str
    customer_phone:str
    status:str
    total_price:int

class OrderStatusSchema(BaseModel):
    status: str      #separate schema for when an admin is changing status of item

#create a single product 
@router.post("/order")
def create_order(order:OrderSchema, session=Depends(get_db)):
    #this is where i will come to use sqlalchemy to create records
    #now the actual code to create records
    # existing=session.query(Order).filter(Order.customer_name==order.customer_name).first()
    
    # if existing is None:


    new_order=Order(customer_name=order.customer_name,
            customer_email=order.customer_email,
            customer_phone=order.customer_phone,
            status="Pending",
            total_price=order.total_price) #creates the instance of the category class
    
    #adds the instance to the transaction
    session.add(new_order)

    #then commits the transaction
    session.commit()
    session.refresh(new_order)

    
    return{"message":"Order made successfully",
           "order_id": new_order.id}

    # else:
    #     return {"message":"order already exists"}

    # removed check since customer is allowed to place as many orders as necessary

#retrieve all orders. Admin can view all orders from all customers
@router.get("/order")
def get_orders(session=Depends(get_db)):
    #here i will use sqlalchemy to retrieve all products
    #code to retrive categories
    orders = (
        session.query(Order)
        .filter(Order.status.in_(["Pending", "Processing"]))
        .all()
    )

    return orders

@router.get("/order/history")
def get_order_history(session=Depends(get_db)):

    orders = (
        session.query(Order)
        .filter(Order.status.in_(["Completed", "Cancelled"]))
        .all()
    )

    return orders

#retrieve a single order
@router.get("/order/{order_id}")#never forget the parameters inside
def get_order(order_id, session=Depends(get_db)):
    order=session.query(Order).filter(Order.id==order_id).first()
    return order

#update a single order. Admin can update status of the order 
@router.patch("/order/{order_id}")
def update_order(order_id, data:OrderSchema, session=Depends(get_db)):
    order=session.query(Order).filter(Order.id==order_id).first()

    if not order:
        return{"message":"Order not found"}
    
    # #check to prevent duplicate values
    # if data.name:
    #     exists=session.query(Category).filter(Category.name==data.name ,Category.id!=category_id).first()

    #     if  exists:
    #         return {"message":"name used by another category"}
        
    #     if data.name:
    order.customer_name=data.customer_name
    order.customer_email=data.customer_email
    order.customer_phone=data.customer_phone
    order.status = data.status
        # if data.description is not None:
        #     Category.description==data.description

    session.commit()  
    session.refresh(order)

    return{"message":"order updated successfully"}      

#delete a single order. This end point may never be used since orders are rarely deleted. So i just have it here incase i need to ever use it
@router.delete("/order/{order_id}")
def delete_order(order_id,session=Depends(get_db)):
    order = session.query(Order).filter(Order.id == order_id).first()

    session.delete(order)
    session.commit()

    return {"message": "Order deleted successfully"}  

@router.patch("/order/{order_id}/status")
def update_order_status(
    order_id: int,
    data: OrderStatusSchema,
    session=Depends(get_db)
):
    order = session.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    allowed_statuses = [
        "Pending",
        "Processing",
        "Completed",
        "Cancelled"
    ]

    if data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid order status"
        )

    order.status = data.status

    session.commit()
    session.refresh(order)

    return {
        "message": "Order status updated successfully",
        "order_id": order.id,
        "status": order.status
    } 