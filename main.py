from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./sales_orders.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class OrderItemDB(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("sales_orders.id"))
    product_name = Column(String, index=True)
    quantity = Column(Integer)
    price = Column(Float)

class SalesOrderDB(Base):
    __tablename__ = "sales_orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    order_date = Column(DateTime, default=datetime.utcnow)
    items = relationship("OrderItemDB", backref="order", cascade="all, delete-orphan")

Base.metadata.create_all(bind=engine)

app = FastAPI()

class OrderItem(BaseModel):
    product_name: str
    quantity: int
    price: float

class SalesOrderCreate(BaseModel):
    customer_name: str
    items: List[OrderItem]

class SalesOrderResponse(BaseModel):
    id: int
    customer_name: str
    order_date: datetime
    items: List[OrderItem]

    class Config:
        orm_mode = True

@app.post("/sales_orders/", response_model=SalesOrderResponse)
def create_sales_order(order: SalesOrderCreate):
    db = SessionLocal()
    db_order = SalesOrderDB(customer_name=order.customer_name)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    for item in order.items:
        db_item = OrderItemDB(
            order_id=db_order.id,
            product_name=item.product_name,
            quantity=item.quantity,
            price=item.price
        )
        db.add(db_item)
    db.commit()
    db.refresh(db_order)
    db_order.items  # Load items
    db.close()
    return db_order

@app.get("/sales_orders/{order_id}", response_model=SalesOrderResponse)
def get_sales_order(order_id: int):
    db = SessionLocal()
    db_order = db.query(SalesOrderDB).filter(SalesOrderDB.id == order_id).first()
    if not db_order:
        db.close()
        raise HTTPException(status_code=404, detail="Order not found")
    db_order.items  # Load items
    db.close()
    return db_order
