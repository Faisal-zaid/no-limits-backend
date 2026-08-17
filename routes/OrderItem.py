from fastapi import APIRouter, Depends
from models import OrderItem, get_db
from pydantic import BaseModel

router = APIRouter()