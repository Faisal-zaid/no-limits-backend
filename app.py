#import fastapi class
from fastapi import FastAPI, Depends # Depnds is added so records are persisted to the database
#imports the classes from models
from models import get_db,Category, Product, ProductField, ProductFieldOption, Order, OrderItem, OrderItemFieldValue 
#we need to do data validation using pydantic
from pydantic import BaseModel
#this import allows enabling of CORS
from fastapi.middleware.cors import CORSMiddleware
#tells fastapi of the separate route that will communicate to it
from routes.Category import router as category_router

#create an instance
app=FastAPI()

#allow access from all servers
app.add_middleware(CORSMiddleware,  allow_origins=["*"],allow_methods=["*"])

#create routes and access resources 
@app.get("/")
def read_root():
    return{"Hello":"world!"}

