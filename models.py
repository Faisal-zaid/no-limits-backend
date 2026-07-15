#import necessary packages
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column,Integer,Text,DateTime

#set up base class where models will inherit from
Base=declarative_base()

#begining of modelling the clases
class Category(Base):
    __tablename__="categories"

    id=Column(Integer, primary_key=True, index=True)
    name=Column(String, nullable=False, unique=True)
    description=Column(Text)
    image=Column(String)

    products=relationship("Product", back_populates="category")

class Product(Base):
    __tablename__="products"  

    id=Column(Integer,Primary_key=True, index=True)
    category_id=Column(Integer, ForeignKey("categories.id"))

    name=Column(Text, nullable=False)
    description=Column(Text)
    base_price=Column(Integer)
    image=Column(String)

    category=relationship("Category", back_populates="products")

    fields=relationship(
        "ProductField",
        back_populates="product",
        cascade="all, delete-orphan"
    )
