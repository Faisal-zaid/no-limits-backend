import os
from dotenv import load_dotenv
from models import User, get_db
from pydantic import BaseModel
from fastapi import APIRouter,FastAPI, Depends, Request,HTTPException,status,Response # Depnds is added so records are persisted to the database
#below are imports that allow authentication and authorization
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm   #fastapi uses this request form to safely read login details
from datetime import datetime,timedelta,timezone
from typing_extensions import Annotated
from jose import jwt ,JWTError
from passlib.context import CryptContext  
from typing import List

from fastapi.responses import JSONResponse  #FastAPI puts the JWT into an HttpOnly cookie.


from sqlalchemy.orm import Session

load_dotenv(override=True)

router = APIRouter()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM="HS256"

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")  #unused since i switched to http

#setup password context(bycrpt) and secret key for signing context

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

# hashed_password = pwd_context.hash(password)

# print(hashed_password)


#FAKe db to be removed


class UserSchema(BaseModel):
    username:str
    email:str
    hashed_password:str
    role:str

class RegisterSchema(BaseModel):
    username: str
    email: str
    password: str

    

#the login route
@router.post("/token")
async def login(response: Response,form_data:Annotated[OAuth2PasswordRequestForm,Depends()],
                db: Annotated[Session, Depends(get_db)]):
     user = db.query(User).filter(
          User.username == form_data.username
           ).first()
     if not user:
        raise HTTPException(status_code=400,detail="incorrect username")
     

    #verify  password using bycrpt

     password_matches=pwd_context.verify(form_data.password,user.hashed_password)

     if not password_matches:
            raise HTTPException(status_code=400, detail="Incorrect password")

    #creatte the jtw
     expire_time=datetime.now(timezone.utc)+timedelta(minutes=15)
     token_data={"sub":user.username,"exp":expire_time}

    #sign with our secret key so no one can forge it

     encoded_jwt=jwt.encode(token_data, SECRET_KEY,algorithm=ALGORITHM)

     response.set_cookie(
        key="access_token",
        value=encoded_jwt,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=900
    )  #response.set_cookie i have added to allow cookies to store jwt, in login route above i also added 'response: Response'

#RETURN TO THE USER
     return {"message":"login successful"}

#dependency function
async def get_current_user(request: Request,
                           db: Annotated[Session, Depends(get_db)]):

    token = request.cookies.get("access_token")

    credentials_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="could not validate credentials",
        headers={"WWW-Authenticate":"Bearer"}
    )

 # No cookie = not logged in
    if not token:
        raise credentials_exception

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
    user = db.query(User).filter(
        User.username == username
    ).first()

    if user is None:
        raise credentials_exception
    return user

#a protected endpoint
@router.get("/users/me")
async def read_users_me(current_user:Annotated[User,
                                               Depends(get_current_user)]):
    #this code only runs if token was valid
    return current_user

#authorization dependancy helper
class RoleChecker:
    def __init__(self, allowed_roles:List[str]):
        self.allowed_roles=allowed_roles
    def __call__(self,current_user:Annotated[dict,
                                            Depends(get_current_user)]):
    #checks if user role is allowed 
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access"
        )
        return current_user

#create specific permission gates
allow_admin=RoleChecker(["admin"])
allow_any_user=RoleChecker(["admin","customer"])

#endpoints with authorization
@router.get('/dashboard')
async def view_dashboard(current_user:Annotated[dict,Depends(allow_any_user)]):
    return {
    "message": f"welcome to your dashboard,{current_user.username}!"
}

@router.get('/admin/settings')
async def view_admin_settings(current_user:Annotated[dict,Depends(allow_admin)]):
    return {"message":"welcome to admin panel"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "logged out successfully"}
