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
