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
from routes.Product import router as product_router
from routes.ProductField import router as productfield_router
from routes.ProductFieldOption import router as productfieldoption_router
from routes.Order import router as order_router
from routes.Checkout import router as checkout_router

#create an instance
app=FastAPI()

#acts as blueprint for the route
app.include_router(category_router)
app.include_router(product_router)
app.include_router(order_router)
app.include_router(productfield_router)
app.include_router(productfieldoption_router)
app.include_router(checkout_router)

#allow access from all servers
app.add_middleware(CORSMiddleware,  allow_origins=["*"],allow_methods=["*"])

#create routes and access resources 
@app.get("/")
def read_root():
    return{"Hello":"world!"}

