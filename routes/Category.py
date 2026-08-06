from fastapi import APIRouter, Depends #the APIRouter allows us to use routes easily than relying everything in app.py
from models import Category, get_db
from pydantic import BaseModel
import cloudinary.uploader
import cloudinary_config
from fastapi import UploadFile, File, Form

router=APIRouter()

#for validation of category i will do 
# class CategorySchema(BaseModel):
#     name:str
#     description:str
#     image:str
#     subheading:str
#create a single category 
@router.post("/category")
def create_category(name:str=Form(...),
                    description:str=Form(...),
                    subheading:str=Form(...),
                    image:UploadFile=File(...),
                    session=Depends(get_db)):
    #this is where i will come to use sqlalchemy to create records
    #now the actual code to create records
    existing=session.query(Category).filter(Category.name==name).first()
    
    if existing :
        return {"message":"category exists"}

    result=cloudinary.uploader.upload(image.file)

    new_category=Category(name=name,
                          description=description,
                          subheading=subheading,
                          image=result["secure url"]
                          ) #creates the instance of the category class
    
    #adds the instance to the transaction
    session.add(new_category)

    #then commits the transaction
    session.commit()
    
    return{"message":"Category created successfully" }
    



#retrieve all categories
@router.get("/category")
def get_categories(session=Depends(get_db)):
    #here i will use sqlalchemy to retrieve all categories
    #code to retrive categories
    categories=session.query(Category).all()
    return categories

#retrieve a single category
@router.get("/category/{category_id}")#never forget the parameters inside
def get_category(category_id, session=Depends(get_db)):
    category=session.query(Category).filter(Category.id==category_id).first()
    return category

#update a single category
@router.patch("/category/{category_id}")
def update_category(category_id, data:CategorySchema, session=Depends(get_db)):
    category=session.query(Category).filter(Category.id==category_id).first()

    if not Category:
        return{"message":"Category not found"}
    
    # #check to prevent duplicate values
    # if data.name:
    #     exists=session.query(Category).filter(Category.name==data.name ,Category.id!=category_id).first()

    #     if  exists:
    #         return {"message":"name used by another category"}
        
    #     if data.name:
    category.name=data.name
    category.description=data.description
    category.image=data.image
    category.subheading=data.subheading
        # if data.description is not None:
        #     Category.description==data.description

    session.commit()  
    session.refresh(category)

    return{"message":"category updated successfully"}      

#delete a single category
@router.delete("/category/{category_id}")
def delete_category(category_id,session=Depends(get_db)):
    category = session.query(Category).filter(Category.id == category_id).first()

    session.delete(category)
    session.commit()

    return {"message": "Category deleted successfully"}   