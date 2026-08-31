import os
from dotenv import load_dotenv
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
from jose import jwt ,JWTError
from passlib.context import CryptContext  



from routes.Category import router as category_router
from routes.Product import router as product_router
from routes.ProductField import router as productfield_router
from routes.ProductFieldOption import router as productfieldoption_router
from routes.Order import router as order_router
from routes.checkout import router as checkout_router
from routes.OrderItem import router as orderitem_router
from routes.OrderItemFieldValue import router as orderitemfieldvalue_router

load_dotenv(override=True)

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


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM="HS256"

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

#setup password context(bycrpt) and secret key for signing context

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

# hashed_password = pwd_context.hash(password)

# print(hashed_password)


#FAKe db to be removed

FAKE_USER_DB={
    "alice":{
        "username":"alice",
        "email":"alice@example.com",
        "role":"admin",
        "hashed_password":"$2b$12$bia9eIa7AR.vpJEBK3EhbOkNtVarFw2gBR3nH6chKtE9Ivs08SKdi"
    },
    "bob":{
        "username":"bob",
        "email":"bob@example.com",
        "role":"customer",
        "hashed_password":"$2b$12$bia9eIa7AR.vpJEBK3EhbOkNtVarFw2gBR3nH6chKtE9Ivs08SKdi"
    }
}

#the login route
@app.post("/token")
async def login(form_data:Annotated[OAuth2PasswordRequestForm,Depends()]):
    user=FAKE_USER_DB.get(form_data.username)
    if not user:
        raise HTTPException(status_code=400,detail="incorrect username")

    #verify  password using bycrpt

    password_matches=pwd_context.verify(form_data.password,user["hashed_password"])

    if not password_matches:
        raise HTTPException(status_code=400, detail="Incorrect password")

    #creatte the jtw
    expire_time=datetime.now(timezone.utc)+timedelta(minutes=15)
    token_data={"sub":user["username"],"exp":expire_time}

    #sign with our secret key so no one can forge it

    encoded_jwt=jwt.encode(token_data, SECRET_KEY,algorithm=ALGORITHM)

#RETURN TO THE USER
    return {"access_token":encoded_jwt,"token_type":"bearer"}

#dependency function
async def get_current_user(token:Annotated[str,Depends(oauth2_scheme)]):
    credentials_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="could not validate credentials",
        headers={"WWW-Authenticate":"Bearer"}
    )
    try:
        #decode token using secret key
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username:str=payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        #if the token is altered expired or fake it will fail here
        raise credentials_exception

    #look up the user in the db using username from token
    user=FAKE_USER_DB.get(username)
    if user is None:
        raise credentials_exception
    return user

#a protected endpoint
@app.get("/users/me")
async def read_users_me(current_user:Annotated[dict,
                                               Depends(get_current_user)]):
    #this code only runs if token was valid
    return current_user

#authorization dependancy helper
class RoleChecker:
    def__init__(self, allowed_roles:list[str]):
        self.allowed_roles=allowed_roles
    def__call__(self,current_user:Annotated[dict,
                                            Depends(get_current_user)]):
    #checks if user role is allowed 
    if current_user.get("role")not in self.allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            details="No permission to access"
        )
    return current_user


#apply to a route using custom identifier and callback in 
#create routes and access resources 
@app.get("/",
         dependencies=[
             Depends(RateLimiter(times=10,minutes=1,identifier=get_user_id_identifier,callback=custom_callback))
         ])
def read_root(token:str=Depends(oauth2_scheme)):
    return{"Hello":"world!"}

