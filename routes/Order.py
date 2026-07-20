from fastapi import APIRouter, Depends #the APIRouter allows us to use routes easily than relying everything in app.py
from models import Order, get_db
from pydantic import BaseModel

router=APIRouter()

#for validation of Order i will do 
class OrderSchema(BaseModel):
    customer_name=str
    customer_email=str
    customer_phone=str
    status=str
    total_price=int
#create a single product 
@router.post("/order")
def create_order(order:OrderSchema, session=Depends(get_db)):
    #this is where i will come to use sqlalchemy to create records
    #now the actual code to create records
    existing=session.query(Order).filter(Order.name==order.name).first()
    
    if existing is None:

        new_order=Order(name=order.name) #creates the instance of the category class
    
    #adds the instance to the transaction
        session.add(new_order)

    #then commits the transaction
        session.commit()
    
        return{"message":"Order made successfully"}

    else:
        return {"message":"order already exists"}

#retrieve all products
@router.get("/product")
def get_products(session=Depends(get_db)):
    #here i will use sqlalchemy to retrieve all products
    #code to retrive categories
    products=session.query(Product).all()
    return products

#retrieve a single product
@router.get("/product/{product_id}")#never forget the parameters inside
def get_product(product_id, session=Depends(get_db)):
    product=session.query(Product).filter(Product.id==product_id).first()
    return product

#update a single product
@router.patch("/product/{product_id}")
def update_product(product_id, data:ProductSchema, session=Depends(get_db)):
    product=session.query(Product).filter(Product.id==product_id).first()

    if not Product:
        return{"message":"Product not found"}
    
    # #check to prevent duplicate values
    # if data.name:
    #     exists=session.query(Category).filter(Category.name==data.name ,Category.id!=category_id).first()

    #     if  exists:
    #         return {"message":"name used by another category"}
        
    #     if data.name:
    product.name=data.name
        # if data.description is not None:
        #     Category.description==data.description

    session.commit()  
    session.refresh(product)

    return{"message":"product updated successfully"}      

#delete a single product
@router.delete("/product/{product_id}")
def delete_product(product_id,session=Depends(get_db)):
    product = session.query(Product).filter(Product.id == product_id).first()

    session.delete(product)
    session.commit()

    return {"message": "Product deleted successfully"}   