import os
from dotenv import load_dotenv
#below are imports that allow authentication and authorization
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm   #fastapi uses this request form to safely read login details
from datetime import datetime,timedelta,timezone
from typing import Annotated
from jose import jwt ,JWTError
from passlib.context import CryptContext  

load_dotenv(override=True)

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
    def __init__(self, allowed_roles:list[str]):
        self.allowed_roles=allowed_roles
    def __call__(self,current_user:Annotated[dict,
                                            Depends(get_current_user)]):
    #checks if user role is allowed 
        if current_user.get("role")not in self.allowed_roles:
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access"
        )
        return current_user

#create specific permission gates
allow_admin=RoleChecker(["admin"])
allow_any_user=RoleChecker(["admin","customer"])

#endpoints with authorization
@app.get('/dashboard')
async def view_dashboard(current_user:Annotated[dict,Depends(allow_any_user)]):
    return {"message":f"welcome to your dashboard,{current_user['username']}!"}

@app.get('/admin/settings')
async def view_admin_settings(current_user:Annotated[dict,Depends(allow_admin)]):
    return {"message":"welcome to admin panel"}
