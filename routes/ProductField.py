from fastapi import APIRouter, Depends #the APIRouter allows us to use routes easily than relying everything in app.py
from models import ProductField, get_db
from pydantic import BaseModel

router=APIRouter()

#for validation of productfield i will do 
class ProductFieldSchema(BaseModel):
    product_id:int
    label:str
    field_type:str
    required:bool
    placeholder:str
#create a single product
@router.post("/productfield")
def create_productfield(productfield:ProductFieldSchema, session=Depends(get_db)):
    #this is where i will come to use sqlalchemy to create records
    #now the actual code to create records
    existing=session.query(ProductField).filter(ProductField.name==productfield.name).first()
    
    if existing is None:

        new_productfield=ProductField(name=productfield.name) #creates the instance of the category class
    
    #adds the instance to the transaction
        session.add(new_productfield)

    #then commits the transaction
        session.commit()
    
        return{"message":"Product field created successfully"}

    else:
        return {"message":"Product field already exists"}

#retrieve all products
@router.get("/productfield")
def get_productsfield(session=Depends(get_db)):
    #here i will use sqlalchemy to retrieve all products
    #code to retrive productfields
    productsfield=session.query(ProductField).all()
    return productsfield

#retrieve a single product
@router.get("/productfield/{productfield_id}")#never forget the parameters inside
def get_productfield(productfield_id, session=Depends(get_db)):
    productfield=session.query(ProductField).filter(ProductField.id==productfield_id).first()
    return productfield

#update a single product field
@router.patch("/productfield/{productfield_id}")
def update_productfield(productfield_id, data:ProductFieldSchema, session=Depends(get_db)):
    productfield=session.query(ProductField).filter(ProductField.id==productfield_id).first()

    if not ProductField:
        return{"message":"ProductField not found"}
    
    # #check to prevent duplicate values
    # if data.name:
    #     exists=session.query(Category).filter(Category.name==data.name ,Category.id!=category_id).first()

    #     if  exists:
    #         return {"message":"name used by another category"}
        
    #     if data.name:
    productfield.name=data.name
        # if data.description is not None:
        #     Category.description==data.description

    session.commit()  
    session.refresh(productfield)

    return{"message":"product field updated successfully"}      

#delete a single product
@router.delete("/productfield/{productfield_id}")
def delete_productfield(productfield_id,session=Depends(get_db)):
    productfield = session.query(ProductField).filter(ProductField.id == productfield_id).first()

    session.delete(productfield)
    session.commit()

    return {"message": "Product field deleted successfully"}   