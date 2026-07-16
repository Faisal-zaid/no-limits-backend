#import fastapi class
from fastapi import FastAPI

#create an instance
app=FastAPI()

#create routes and access resources 
@app.get("/")
def read_root():
    return{"Hello":"world!"}