from fastapi import APIRouter, Depends #the APIRouter allows us to use routes easily than relying everything in app.py
from models import ProductFieldOption, get_db
from pydantic import BaseModel

router=APIRouter()

#for validation of product field option i will do 
class ProductFieldOptionSchema(BaseModel):
    value:str
    
#create a single product-field-option
@router.post("/productfieldoption")
def create_productfieldoption(productfieldoption:ProductFieldOptionSchema, session=Depends(get_db)):
    #this is where i will come to use sqlalchemy to create records
    #now the actual code to create records
    existing=session.query(ProductFieldOption).filter(ProductFieldOption.name==productfieldoption.name).first()
    
    if existing is None:

        new_productfield=ProductFieldOption(name=productfieldoption.name) #creates the instance of the category class
    
    #adds the instance to the transaction
        session.add(new_productfieldoption)

    #then commits the transaction
        session.commit()
    
        return{"message":"Product field option created successfully"}

    else:
        return {"message":"Product field option already exists"}

#retrieve all productfieldoptions
@router.get("/productfieldoption")
def get_productsfieldoption(session=Depends(get_db)):
    #here i will use sqlalchemy to retrieve all products
    #code to retrive productfields
    productsfieldoption=session.query(ProductFieldOption).all()
    return productsfieldoption

#retrieve a single product field option
@router.get("/productfieldoption/{productfieldoption_id}")#never forget the parameters inside
def get_productfieldoption(productfieldoption_id, session=Depends(get_db)):
    productfieldoption=session.query(ProductFieldOption).filter(ProductFieldOption.id==productfieldoption_id).first()
    return productfieldoption

#update a single productfieldoption
@router.patch("/productfieldoption/{productfieldoption_id}")
def update_productfieldoption(productfieldoption_id, data:ProductFieldOptionSchema, session=Depends(get_db)):
    productfieldoption=session.query(ProductFieldOption).filter(ProductFieldOption.id==productfieldoption_id).first()

    if not ProductFieldOption:
        return{"message":"ProductFieldOption not found"}
    
    # #check to prevent duplicate values
    # if data.name:
    #     exists=session.query(Category).filter(Category.name==data.name ,Category.id!=category_id).first()

    #     if  exists:
    #         return {"message":"name used by another category"}
        
    #     if data.name:
    productfieldoption.name=data.name
        # if data.description is not None:
        #     Category.description==data.description

    session.commit()  
    session.refresh(productfieldoption)

    return{"message":"product-field-option updated successfully"}      

#delete a single product
@router.delete("/productfieldoption/{productfieldoption_id}")
def delete_productfieldoption(productfieldoption_id,session=Depends(get_db)):
    productfieldoption = session.query(ProductFieldOption).filter(ProductFieldOption.id == productfieldoption_id).first()

    session.delete(productfieldoption)
    session.commit()

    return {"message": "Product-field-option deleted successfully"}   