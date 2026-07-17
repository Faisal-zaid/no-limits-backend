from fastapi import APIRouter, Depends


#for validation of category i will do 
class CategorySchema(BaseModel):
    name:str
#create a single category 
@app.post("/category")
def create_category(category:CategorySchema, session=Depends(get_db)):
    #this is where i will come to use sqlalchemy to create records
    #now the actual code to create records
    existing=session.query(Category).filter(Category.name==category.name).first()
    
    if existing is None:

        new_category=Category(name=category.name) #creates the instance of the category class
    
    #adds the instance to the transaction
        session.add(new_category)

    #then commits the transaction
        session.commit()
    
        return{"message":"Category created successfully"}

    else:
        return {"message":"category already exists"}

#retrieve all categories
@app.get("/category")
def get_categories(session=Depends(get_db)):
    #here i will use sqlalchemy to retrieve all categories
    #code to retrive categories
    categories=session.query(Category).all()
    return categories

#retrieve a single category
@app.get("/category/{category_id}")#never forget the parameters inside
def get_category(category_id, session=Depends(get_db)):
    category=session.query(Category).filter(Category.id==category_id).first()
    return category

#update a single category
@app.patch("/category/{category_id}")
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
        # if data.description is not None:
        #     Category.description==data.description

    session.commit()  
    session.refresh(category)

    return{"message":"category updated successfully"}      

#delete a single category
@app.delete("/category/{category_id}")
def delete_category(category_id,session=Depends(get_db)):
    category = session.query(Category).filter(Category.id == category_id).first()

    session.delete(category)
    session.commit()

    return {"message": "Category deleted successfully"}   