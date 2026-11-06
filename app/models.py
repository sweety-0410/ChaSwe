from datetime import datetime
from sqlalchemy import String,Integer,Boolean,DateTime,ForeignKey,Text,Numeric
from sqlalchemy.orm import Mapped,mapped_column,relationship
from .db import Base
class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(100))
    email:Mapped[str]=mapped_column(String(255),unique=True,index=True)
    password_hash:Mapped[str]=mapped_column(String(255))
    is_admin:Mapped[bool]=mapped_column(Boolean,default=False)
class Product(Base):
    __tablename__="products"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(140))
    category:Mapped[str]=mapped_column(String(80),default="Classics")
    description:Mapped[str]=mapped_column(Text,default="")
    price:Mapped[float]=mapped_column(Numeric(10,2))
    image_url:Mapped[str]=mapped_column(String(500),default="")
    stock:Mapped[int]=mapped_column(Integer,default=0)
    active:Mapped[bool]=mapped_column(Boolean,default=True)
class CartItem(Base):
    __tablename__="cart_items"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    product_id:Mapped[int]=mapped_column(ForeignKey("products.id",ondelete="CASCADE"))
    quantity:Mapped[int]=mapped_column(Integer,default=1)
    product=relationship("Product")
class Order(Base):
    __tablename__="orders"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
    name:Mapped[str]=mapped_column(String(120))
    phone:Mapped[str]=mapped_column(String(30))
    address:Mapped[str]=mapped_column(Text)
    city:Mapped[str]=mapped_column(String(100))
    pincode:Mapped[str]=mapped_column(String(20))
    subtotal:Mapped[float]=mapped_column(Numeric(10,2))
    shipping:Mapped[float]=mapped_column(Numeric(10,2))
    total:Mapped[float]=mapped_column(Numeric(10,2))
    status:Mapped[str]=mapped_column(String(40),default="Placed")
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    items=relationship("OrderItem",cascade="all, delete-orphan")
class OrderItem(Base):
    __tablename__="order_items"
    id:Mapped[int]=mapped_column(primary_key=True)
    order_id:Mapped[int]=mapped_column(ForeignKey("orders.id",ondelete="CASCADE"))
    product_name:Mapped[str]=mapped_column(String(140))
    price:Mapped[float]=mapped_column(Numeric(10,2))
    quantity:Mapped[int]=mapped_column(Integer)
