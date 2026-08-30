#import fastapi class

from fastapi import FastAPI, Depends, Request,HTTPException,status # Depnds is added so records are persisted to the database
#imports the classes from models
from models import engine,Base ,get_db,Category, Product, ProductField, ProductFieldOption, Order, OrderItem, OrderItemFieldValue 
#we need to do data validation using pydantic
from pydantic import BaseModel
#this import allows enabling of CORS
from fastapi.middleware.cors import CORSMiddleware
#tells fastapi of the separate route that will communicate to it
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis   # they allow us to use ratelimiters

#below are imports that allow authentication and authorization
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm   #fastapi uses this request form to safely read login details
from datetime import datetime,timedelta,timezone
from typing import Annotated
from jose import jwt 
from passlib.context import CryptContext  



from routes.Category import router as category_router
from routes.Product import router as product_router
from routes.ProductField import router as productfield_router
from routes.ProductFieldOption import router as productfieldoption_router
from routes.Order import router as order_router
from routes.checkout import router as checkout_router
from routes.OrderItem import router as orderitem_router
from routes.OrderItemFieldValue import router as orderitemfieldvalue_router


Base.metadata.create_all(bind=engine)  #this line creates a missing table suppose the backend is in production


#create an instance
app=FastAPI()

@app.on_event("startup")
async def startup():
    redis_connection = redis.from_url(
        "redis://localhost:6379",
        encoding="utf-8",
        decode_responses=True
    )

    await FastAPILimiter.init(redis_connection) #initializes redis to work with rate limiter

#acts as blueprint for the route
app.include_router(category_router)
app.include_router(product_router)
app.include_router(order_router)
app.include_router(productfield_router)
app.include_router(productfieldoption_router)
app.include_router(checkout_router)
app.include_router(orderitem_router)
app.include_router(orderitemfieldvalue_router)

#allow access from all servers
app.add_middleware(CORSMiddleware,  allow_origins=["*"],allow_headers=["*"],allow_methods=["*"])



# app.mount(
#     "/uploads",
#     StaticFiles(directory="uploads"),
#     name="uploads"
# )     #if you database has /uploads/yaga   the online link will be {link}/uploads/yaga


#rate limiter code below 

#custom identifier that pulls user id from request state or headers
async def get_user_id_identifier(request:Request)->str:
    if hasattr(request.state,"user")and request.state.user:
        return f"user:{request.state.user.id}"

#fallbacks to ip if user hasnet logged in or registered
    auth_header=request.headers.get("Authorization")
    if auth_header:
        return f"token:{auth_header}"   
    return f"ip:{request.client.host}" 

#custom callback:changes the default 429 error message
async def custom_callback(request:Request,response,pexpire:int):
    #pexpire is the milliseconds left till the rate limit resets
    seconds_left=max(1,pexpire//1000)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error":"slow down!",
            "message":f"You have exceeded your limit, please try again in {seconds_left}seconds.",
            "retry_after_seconds":seconds_left
        }
    )

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

#setup password context(bycrpt) and secret key for signing context

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
SECRET_KEY=''
ALGORITHM=""

#FAKe db to be removed

#apply to a route using custom identifier and callback in 
#create routes and access resources 
@app.get("/",
         dependencies=[
             Depends(RateLimiter(times=10,minutes=1,identifier=get_user_id_identifier,callback=custom_callback))
         ])
def read_root(token:str=Depends(oauth2_scheme)):
    return{"Hello":"world!"}

