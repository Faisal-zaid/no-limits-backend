#import necessary packages
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column,Integer,Text,DateTime,String,ForeignKey,Boolean,create_engine
from datetime import datetime

#set up base class where models will inherit from
Base=declarative_base()

#begining of modelling the clases
class Category(Base):# stores the main service categories that the business offers
    __tablename__="categories"

    id=Column(Integer, primary_key=True, index=True)
    name=Column(String, nullable=False, unique=True)
    description=Column(Text)
    image=Column(String)

    products=relationship("Product", back_populates="category")

class Product(Base):# stores the services or products under a category
    __tablename__="products"  

    id=Column(Integer,primary_key=True, index=True)
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

class ProductField(Base):#stores the custom field created by admin for each product
    __tablename__="product_fields"

    id=Column(Integer, primary_key=True, index=True)
    product_id=Column(Integer, ForeignKey("products.id"))
    label=Column(String, nullable=False)
    field_type=Column(String, nullable=False)
    required=Column(Boolean, default=False)
    placeholder=Column(String)
    
    product=relationship("Product",back_populates="fields")

    options=relationship(
        "ProductFieldOption",
        back_populates="field",
        cascade="all, delete-orphan"
    )    

class ProductFieldOption(Base):#some field types will be dropdowns so here is where the custom options of drop downs are stored
    __tablename__="product_field_options"

    id=Column(Integer, primary_key=True)
    field_id=Column(Integer, ForeignKey("product_fields.id"))
    value=Column(String, nullable=False)
    field=relationship("ProductField", back_populates="options") 

class Order(Base): #stores sinformation about a customers order
    __tablename__="orders"       

    id=Column(Integer, primary_key=True)
    customer_name=Column(String)
    customer_email=Column(String)
    customer_phone=Column(String)
    status=Column(String, default="Pending")
    total_price=Column(Integer)
    created_at=Column(DateTime, default=datetime.now()) #from datetime import datetime - this is what makes that line possible

    items=relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )

class OrderItem(Base): #stores each product inside an order, e.g an order can have 3 products
    __tablename__="order_items"

    id=Column(Integer, primary_key=True)
    order_id=Column(Integer, ForeignKey("orders.id"))
    product_id=Column(Integer, ForeignKey("products.id"))
    quantity=Column(Integer)
    order=relationship("Order", back_populates="items")
    product=relationship("Product")

    values=relationship(
        "OrderItemFieldValue",
        back_populates="order_item",
        cascade="all, delete-orphan"
    )    

class OrderItemFieldValue(Base): # customers answer to each custom field that was provided
    __tablename__="order_item_field_values"

    id=Column(Integer, primary_key=True)
    order_item_id=Column(Integer, ForeignKey("order_items.id"))
    product_field_id=Column(Integer, ForeignKey("product_fields.id"))
    value=Column(Text)
    order_item=relationship("OrderItem", back_populates="values")
    product_field=relationship("ProductField")    
