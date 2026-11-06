import os,re
from decimal import Decimal
from datetime import datetime,timedelta,timezone
from fastapi import FastAPI,Depends,HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel,EmailStr,Field
from sqlalchemy.orm import Session
from jose import jwt,JWTError
from passlib.context import CryptContext
from .db import Base,engine,get_db,Session as DBSession
from .models import User,Product,CartItem,Order,OrderItem

app=FastAPI(title="ChaSwe Store")
app.mount("/static",StaticFiles(directory="static"),name="static")
pwd=CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth=OAuth2PasswordBearer(tokenUrl="/api/login")
SECRET=os.getenv("SECRET_KEY","dev-only-change-me")
def token(uid): return jwt.encode({"sub":str(uid),"exp":datetime.now(timezone.utc)+timedelta(days=7)},SECRET,algorithm="HS256")
def current(t:str=Depends(oauth),db:Session=Depends(get_db)):
    try: uid=int(jwt.decode(t,SECRET,algorithms=["HS256"])["sub"])
    except Exception: raise HTTPException(401,"Please sign in")
    u=db.get(User,uid)
    if not u: raise HTTPException(401,"Please sign in")
    return u
def admin(u:User=Depends(current)):
    if not u.is_admin: raise HTTPException(403,"Admin only")
    return u
class Register(BaseModel):
    name:str=Field(min_length=2,max_length=100)
    email:EmailStr
    password:str=Field(min_length=8,max_length=128)
class Login(BaseModel):
    email:EmailStr
    password:str
class ProductData(BaseModel):
    name:str=Field(min_length=2,max_length=140)
    category:str="Classics"
    description:str=""
    price:float=Field(gt=0)
    image_url:str=""
    stock:int=Field(ge=0)
class CartData(BaseModel):
    product_id:int
    quantity:int=Field(ge=1,le=50)
class Checkout(BaseModel):
    name:str=Field(min_length=2)
    phone:str=Field(min_length=8)
    address:str=Field(min_length=8)
    city:str
    pincode:str=Field(min_length=4)
@app.on_event("startup")
def start():
    Base.metadata.create_all(engine)
    db=DBSession()
    if db.query(Product).count()==0:
        db.add_all([
          Product(name="Classic Choco Chip",category="Classics",description="Golden, buttery cookies with generous chocolate chips.",price=149,stock=40,image_url="https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=900"),
          Product(name="Double Chocolate",category="Chocolate",description="Rich cocoa cookies with pools of chocolate.",price=169,stock=30,image_url="https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=900"),
          Product(name="Cashew Crunch",category="Nutty",description="Crisp edges, roasted cashew pieces, lots of comfort.",price=179,stock=24,image_url="https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=900"),
          Product(name="Oat & Raisin",category="Wholesome",description="A cosy, chewy cookie with oats and raisins.",price=159,stock=20,image_url="https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=900")])
    email=os.getenv("ADMIN_EMAIL","admin@chaswe.local").lower()
    if not db.query(User).filter_by(email=email).first():
        db.add(User(name=os.getenv("ADMIN_NAME","ChaSwe Admin"),email=email,password_hash=pwd.hash(os.getenv("ADMIN_PASSWORD","ChangeThisPassword123!")),is_admin=True))
    db.commit();db.close()
@app.get("/")
def home(): return FileResponse("static/index.html")
@app.get("/api/health")
def health(): return {"status":"ok"}
def prod(p): return {"id":p.id,"name":p.name,"category":p.category,"description":p.description,"price":float(p.price),"image_url":p.image_url,"stock":p.stock}
@app.get("/api/products")
def products(category:str="All",search:str="",db:Session=Depends(get_db)):
    q=db.query(Product).filter(Product.active==True)
    if category!="All": q=q.filter(Product.category==category)
    if search: q=q.filter(Product.name.ilike(f"%{search}%"))
    return [prod(p) for p in q.all()]
@app.post("/api/register")
def register(d:Register,db:Session=Depends(get_db)):
    email=d.email.lower()
    if db.query(User).filter_by(email=email).first(): raise HTTPException(409,"Email already registered")
    u=User(name=d.name,email=email,password_hash=pwd.hash(d.password));db.add(u);db.commit();db.refresh(u)
    return {"access_token":token(u.id),"name":u.name,"is_admin":False}
@app.post("/api/login")
def login(d:Login,db:Session=Depends(get_db)):
    u=db.query(User).filter_by(email=d.email.lower()).first()
    if not u or not pwd.verify(d.password,u.password_hash): raise HTTPException(401,"Incorrect email or password")
    return {"access_token":token(u.id),"name":u.name,"is_admin":u.is_admin}
@app.get("/api/me")
def me(u:User=Depends(current)): return {"name":u.name,"email":u.email,"is_admin":u.is_admin}
def cartdata(db,u):
    rows=db.query(CartItem).filter_by(user_id=u.id).all()
    items=[{"product_id":r.product_id,"name":r.product.name,"price":float(r.product.price),"image_url":r.product.image_url,"quantity":r.quantity,"stock":r.product.stock} for r in rows if r.product and r.product.active]
    return {"items":items,"subtotal":round(sum(i["price"]*i["quantity"] for i in items),2)}
@app.get("/api/cart")
def cart(db:Session=Depends(get_db),u:User=Depends(current)): return cartdata(db,u)
@app.post("/api/cart")
def add(d:CartData,db:Session=Depends(get_db),u:User=Depends(current)):
    p=db.get(Product,d.product_id)
    if not p or not p.active: raise HTTPException(404,"Product unavailable")
    r=db.query(CartItem).filter_by(user_id=u.id,product_id=p.id).first()
    qty=(r.quantity if r else 0)+d.quantity
    if qty>p.stock: raise HTTPException(400,f"Only {p.stock} left")
    if r:r.quantity=qty
    else:db.add(CartItem(user_id=u.id,product_id=p.id,quantity=d.quantity))
    db.commit();return cartdata(db,u)
@app.put("/api/cart/{pid}")
def change(pid:int,d:CartData,db:Session=Depends(get_db),u:User=Depends(current)):
    r=db.query(CartItem).filter_by(user_id=u.id,product_id=pid).first();p=db.get(Product,pid)
    if not r or not p:raise HTTPException(404,"Cart item missing")
    if d.quantity>p.stock:raise HTTPException(400,f"Only {p.stock} left")
    r.quantity=d.quantity;db.commit();return cartdata(db,u)
@app.delete("/api/cart/{pid}")
def remove(pid:int,db:Session=Depends(get_db),u:User=Depends(current)):
    r=db.query(CartItem).filter_by(user_id=u.id,product_id=pid).first()
    if r:db.delete(r);db.commit()
    return cartdata(db,u)
@app.post("/api/orders")
def order(d:Checkout,db:Session=Depends(get_db),u:User=Depends(current)):
    rows=db.query(CartItem).filter_by(user_id=u.id).all()
    if not rows:raise HTTPException(400,"Your bag is empty")
    sub=Decimal("0")
    for r in rows:
        if not r.product.active or r.quantity>r.product.stock:raise HTTPException(400,f"Stock changed for {r.product.name}")
        sub+=Decimal(str(r.product.price))*r.quantity
    ship=Decimal("0") if sub>=499 else Decimal("40")
    o=Order(user_id=u.id,name=d.name,phone=d.phone,address=d.address,city=d.city,pincode=d.pincode,subtotal=sub,shipping=ship,total=sub+ship,status="Placed")
    db.add(o);db.flush()
    for r in rows:
        db.add(OrderItem(order_id=o.id,product_name=r.product.name,price=r.product.price,quantity=r.quantity))
        r.product.stock-=r.quantity;db.delete(r)
    db.commit();db.refresh(o)
    return {"id":o.id,"status":o.status,"subtotal":float(o.subtotal),"shipping":float(o.shipping),"total":float(o.total),"payment":"Cash on Delivery"}
@app.get("/api/orders")
def orders(db:Session=Depends(get_db),u:User=Depends(current)):
    return [{"id":o.id,"status":o.status,"total":float(o.total),"created_at":o.created_at.isoformat(),"items":[{"name":i.product_name,"quantity":i.quantity} for i in o.items]} for o in db.query(Order).filter_by(user_id=u.id).order_by(Order.id.desc()).all()]
@app.get("/api/admin/products")
def admin_products(db:Session=Depends(get_db),u:User=Depends(admin)):
    return [prod(p) for p in db.query(Product).all()]
@app.post("/api/admin/products")
def create_product(d:ProductData,db:Session=Depends(get_db),u:User=Depends(admin)):
    p=Product(**d.model_dump());db.add(p);db.commit();db.refresh(p);return prod(p)
@app.put("/api/admin/products/{pid}")
def update_product(pid:int,d:ProductData,db:Session=Depends(get_db),u:User=Depends(admin)):
    p=db.get(Product,pid)
    if not p:raise HTTPException(404,"Not found")
    for k,v in d.model_dump().items():setattr(p,k,v)
    db.commit();return prod(p)
@app.delete("/api/admin/products/{pid}")
def archive_product(pid:int,db:Session=Depends(get_db),u:User=Depends(admin)):
    p=db.get(Product,pid)
    if not p:raise HTTPException(404,"Not found")
    p.active=False;db.commit();return {"ok":True}
@app.get("/api/admin/orders")
def all_orders(db:Session=Depends(get_db),u:User=Depends(admin)):
    return [{"id":o.id,"customer":o.name,"phone":o.phone,"address":o.address,"status":o.status,"total":float(o.total)} for o in db.query(Order).order_by(Order.id.desc()).all()]
@app.put("/api/admin/orders/{oid}")
def set_status(oid:int,status:str,db:Session=Depends(get_db),u:User=Depends(admin)):
    if status not in {"Placed","Confirmed","Baking","Out for delivery","Delivered","Cancelled"}:raise HTTPException(400,"Invalid status")
    o=db.get(Order,oid)
    if not o:raise HTTPException(404,"Order not found")
    o.status=status;db.commit();return {"id":oid,"status":status}
