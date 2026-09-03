from fastapi import APIRouter, Depends #the APIRouter allows us to use routes easily than relying everything in app.py
from models import Product, get_db
from pydantic import BaseModel
import cloudinary_config
from fastapi import UploadFile,File,Form
import cloudinary.uploader
from typing import Optional #adding this so i can use "|"  operand

router=APIRouter()

#for validation of product i will do 
class ProductSchema(BaseModel):
    name:str
    category_id:int
    base_price:int
    description:str
    stock: int
    image:str
#create a single product 
@router.post("/product")
def create_product(name:str=Form(...),
                   category_id:int=Form(...),
                   base_price:int=Form(...),
                   stock: int = Form(...),
                   description:str=Form(...),
                   image:UploadFile=File(...),
                   session=Depends(get_db)):
    #this is where i will come to use sqlalchemy to create records
    #now the actual code to create records
 # Check stock
    if stock < 0:
        return {
            "message": "Stock cannot be negative."
        }


    existing=session.query(Product).filter(Product.name==name).first()
    
    if existing :
        return {"message":"product exists"}

    result=cloudinary.uploader.upload(image.file)

    new_product = Product(
    name=name,
    category_id=category_id,
    base_price=base_price,
    stock=stock,
    description=description,
    image=result["secure_url"]
) #creates the instance of the category class
    
    #adds the instance to the transaction
    session.add(new_product)

    #then commits the transaction
    session.commit()
    
    return{"message": "Product created successfully",
        "product_id": new_product.id,
        "name": new_product.name,
        "stock": new_product.stock}

    # else:
    #     return {"message":"Product already exists"}

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
def update_product(product_id:int,
                   name:str=Form(...),
                   category_id:int=Form(...),
                   base_price:int=Form(...),
                    stock: int = Form(...),
                   description:str=Form(...),
                   image: Optional[UploadFile] = File(None),
                   session=Depends(get_db)):
    product=session.query(Product).filter(Product.id==product_id).first()

    if not product:
        return{"message":"Product not found"}

    if stock < 0:
        return {
            "message": "Stock cannot be negative."
        }    
    
    # #check to prevent duplicate values
    # if data.name:
    #     exists=session.query(Category).filter(Category.name==data.name ,Category.id!=category_id).first()

    #     if  exists:
    #         return {"message":"name used by another category"}
        
    #     if data.name:
    product.name=name
    product.category_id=category_id
    product.base_price=base_price
    product.stock = stock
    product.description=description
    if image:
        result=cloudinary.uploader.upload(image.file)
        product.image=result["secure_url"]
        # if data.description is not None:
        #     Category.description==data.description

    session.commit()  
    session.refresh(product)

    return{"message": "Product updated successfully",
        "product_id": product.id,
        "stock": product.stock}      

#delete a single product
@router.delete("/product/{product_id}")
def delete_product(product_id,session=Depends(get_db)):
    product = session.query(Product).filter(Product.id == product_id).first()

    session.delete(product)
    session.commit()

    return {"message": "Product deleted successfully"}   