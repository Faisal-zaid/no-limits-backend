#import necessary packages
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column,Integer,Text,DateTime

#set up base class where models will inherit from
Base=declarative_base()