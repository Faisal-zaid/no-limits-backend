#import fastapi class
from fastapi import FastAPI

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
@app.get("/category/{category_id}")
def get_category(category_id):
    return{}

#update a single category
@app.patch("/category/{category_id}")
def update_category(category_id):
    return{}

#delete a single category
@app.delete("?category/{category_id}")
def delete_category(category_id):
    return {}    