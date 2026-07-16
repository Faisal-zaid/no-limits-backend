#import fastapi class
from fastapi import FastAPI
from models import get_db,Category, Product, ProductField, ProductFieldOption, Order, OrderItem, OrderItemFieldValue 

#create an instance
app=FastAPI()

#create routes and access resources 
@app.get("/")
def read_root():
    return{"Hello":"world!"}

#create a single category 
@app.post("/category")
def create_category():
    #this is where i will come to use sqlalchemy to create records

    return{"message":"Category created successfully"}

#retrieve all categories
@app.get("/category")
def get_categories():
    #here i will use sqlalchemy to retrieve all categories
    return[]

#retrieve a single category
@app.get("/category/{category_id}")#never forget the parameters inside
def get_category(category_id):
    category=db.query(Category).filter(db==category_id).first()
    return{"id":"category_id"}

#update a single category
@app.patch("/category/{category_id}")
def update_category(category_id):
    return{}

#delete a single category
@app.delete("?category/{category_id}")
def delete_category(category_id):
    return {}    